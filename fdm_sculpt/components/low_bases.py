"""Pinned one-millimetre infantry bases and half-millimetre soil relief."""
from .terrain import base_body, terrain_surface

BASE_SOURCES = {
    'aurelian.base-body-20x5@1': ('aurelian.base-body-20x5-plain', 2, 20),
    'aurelian.base-body-20x5-plain@1': ('aurelian.base-body-20x5-plain', 2, 20),
    'aurelian.base-body-4x5@1': ('aurelian.base-body-4x5-plain', 1, 4),
}
TERRAIN_SOURCES = {
    'aurelian.terrain-soil-20x5-738fc95adfe0@3': 4,
    'aurelian.terrain-soil-gallery@4': 5,
    'aurelian.terrain-soil-natural-strip@2': 3,
}


def revised_parts(definitions, seed):
    if type(seed) is not int or seed != 1001:
        raise ValueError('Use the pinned integer seed 1001')
    replacements = {source: base_body(component, version, width=width,
                    length=5, thickness=1, magnet='none')
                    for source, (component, version, width) in BASE_SOURCES.items()}
    for source, version in TERRAIN_SOURCES.items():
        old = definitions[source]
        settings = old.to_dict()['parameters']['recipe']
        args = {key: settings[key] for key in ('width', 'length', 'style',
                'feature_scale', 'density', 'boots', 'spacing')}
        replacements[source] = terrain_surface(old.component_id, version,
                relief_height=.5, seed=seed, **args)
    return replacements
