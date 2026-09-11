"""Topology and signed-volume analysis for generated proof meshes."""
from __future__ import annotations
from collections import defaultdict, deque
from dataclasses import dataclass
import math
from typing import Any, Iterable, Mapping, Sequence
from .formats import Mesh, coerce_mesh


@dataclass(frozen=True, slots=True)
class MeshAnalysis:
    vertex_count: int
    triangle_count: int
    boundary_edges: int
    nonmanifold_edges: int
    inconsistently_oriented_edges: int
    degenerate_triangles: int
    duplicate_triangles: int
    connected_components: int
    signed_volume_mm3: float
    component_signed_volumes_mm3: tuple[float, ...]

    @property
    def watertight(self) -> bool:
        return self.boundary_edges == 0 and self.nonmanifold_edges == 0

    @property
    def manifold(self) -> bool:
        return (
            self.boundary_edges == 0
            and self.nonmanifold_edges == 0
            and self.degenerate_triangles == 0
            and self.duplicate_triangles == 0
        )

    @property
    def outward_facing(self) -> bool:
        return (
            self.inconsistently_oriented_edges == 0
            and bool(self.component_signed_volumes_mm3)
            and all(volume > 0 for volume in self.component_signed_volumes_mm3)
        )

    @property
    def positive_volume(self) -> bool:
        return self.signed_volume_mm3 > 0


def _cross(a: Sequence[float], b: Sequence[float]) -> tuple[float, float, float]:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _signed_tetra_volume(a: Sequence[float], b: Sequence[float], c: Sequence[float]) -> float:
    cross = _cross(b, c)
    return (a[0] * cross[0] + a[1] * cross[1] + a[2] * cross[2]) / 6.0


def analyze_mesh(mesh: Mesh | Any, *, epsilon: float = 1e-12) -> MeshAnalysis:
    mesh = coerce_mesh(mesh)
    edge_faces: dict[tuple[int, int], list[tuple[int, int]]] = defaultdict(list)
    neighbours: list[set[int]] = [set() for _ in mesh.triangles]
    signed_volumes: list[float] = []
    degenerate = 0
    duplicate = 0
    seen_faces: set[tuple[int, int, int]] = set()

    for face_index, (a_index, b_index, c_index) in enumerate(mesh.triangles):
        face_key = tuple(sorted((a_index, b_index, c_index)))
        if face_key in seen_faces:
            duplicate += 1
        seen_faces.add(face_key)
        a, b, c = (mesh.vertices[index] for index in (a_index, b_index, c_index))
        ab = tuple(b[axis] - a[axis] for axis in range(3))
        ac = tuple(c[axis] - a[axis] for axis in range(3))
        cross = _cross(ab, ac)
        if sum(component * component for component in cross) <= epsilon * epsilon:
            degenerate += 1
        signed_volumes.append(_signed_tetra_volume(a, b, c))
        for start, end in ((a_index, b_index), (b_index, c_index), (c_index, a_index)):
            edge = (min(start, end), max(start, end))
            direction = 1 if (start, end) == edge else -1
            edge_faces[edge].append((face_index, direction))

    boundary = sum(len(entries) == 1 for entries in edge_faces.values())
    nonmanifold = sum(len(entries) > 2 for entries in edge_faces.values())
    inconsistent = 0
    for entries in edge_faces.values():
        if len(entries) == 2:
            (first_face, first_direction), (second_face, second_direction) = entries
            neighbours[first_face].add(second_face)
            neighbours[second_face].add(first_face)
            if first_direction == second_direction:
                inconsistent += 1
        elif len(entries) > 2:
            for first_face, _ in entries:
                neighbours[first_face].update(face for face, _ in entries if face != first_face)

    component_volumes: list[float] = []
    unseen = set(range(len(mesh.triangles)))
    while unseen:
        start = min(unseen)
        queue = deque((start,))
        unseen.remove(start)
        volume = 0.0
        while queue:
            face = queue.popleft()
            volume += signed_volumes[face]
            for neighbour in sorted(neighbours[face]):
                if neighbour in unseen:
                    unseen.remove(neighbour)
                    queue.append(neighbour)
        component_volumes.append(volume)

    return MeshAnalysis(
        vertex_count=len(mesh.vertices),
        triangle_count=len(mesh.triangles),
        boundary_edges=boundary,
        nonmanifold_edges=nonmanifold,
        inconsistently_oriented_edges=inconsistent,
        degenerate_triangles=degenerate,
        duplicate_triangles=duplicate,
        connected_components=len(component_volumes),
        signed_volume_mm3=sum(signed_volumes),
        component_signed_volumes_mm3=tuple(component_volumes),
    )
