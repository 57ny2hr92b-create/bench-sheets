"""Diagram fidelity, physical calibration and author input boundaries."""
import copy
import pathlib
import sys
import xml.etree.ElementTree as ET

import pytest
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools import figures

CATALOG = yaml.safe_load((ROOT / 'tests/fixtures/figures.yaml').read_text())


@pytest.mark.parametrize('name', CATALOG)
def test_catalog_is_deterministic_valid_svg_without_mutation(name):
    spec = copy.deepcopy(CATALOG[name])
    svg = figures.render(spec)
    root = ET.fromstring(svg)
    assert root.tag == 'svg' and root.attrib['aria-label']
    assert float(root.attrib['width']) > 0 and float(root.attrib['height']) > 0
    assert figures.render(spec) == svg and spec == CATALOG[name]


@pytest.mark.parametrize('spec', [
    {'gen': 'dimensions', 'width': -1, 'height': 20},
    {'gen': 'dimensions', 'width': True, 'height': 20},
    {'gen': 'dimensions', 'width': '30', 'height': 20},
    {'gen': 'dimensions', 'width': float('inf'), 'height': 20},
    {'gen': 'dimensions', 'width': 20, 'height': 20, 'scale': 0},
    {'gen': 'dimensions', 'width': 20, 'height': 20, 'thickness': -1},
    {'gen': 'cut', 'pan': 'half', 'cols': 2.5, 'rows': 3},
    {'gen': 'cut', 'size': [0, 100], 'cols': 2, 'rows': 3},
    {'gen': 'cut', 'pan': 'half', 'cols': True, 'rows': 3},
    {'gen': 'cut', 'pan': 'half', 'cols': 2, 'rows': 3, 'first_cuts': 'false'},
    {'gen': 'tray', 'pan': 'half', 'cols': 2, 'rows': 3, 'piece': -2},
    {'gen': 'tray', 'pan': 'half', 'cols': 2, 'rows': 3, 'piece': [20]},
    {'gen': 'tray', 'pan': 'half', 'cols': 2, 'rows': 3, 'piece': 20, 'gap': float('nan')},
    {'gen': 'section', 'layers': [['sponge', float('nan')]]},
    {'gen': 'section', 'layers': [['sponge', True]]},
    {'gen': 'section', 'layers': [[[], 20]]},
    {'gen': 'gauge', 'diameters': [float('nan')]},
    {'gen': 'gauge', 'oblongs': [[30]]},
    {'gen': 'gauge', 'diameters': [30], 'scale': 0.5},
    {'gen': 'fold', 'kind': []},
    {'gen': []},
    {'gen': 'dimensions', 'width': 1e308, 'height': 1, 'scale': 10},
    {'gen': 'gauge', 'diameters': [1e308]},
    {'gen': 'section', 'layers': [['sponge', 1e308]], 'scale': 10},
    None,
])
def test_bad_geometry_is_a_figure_error(spec):
    with pytest.raises(figures.FigureError):
        figures.render(spec)


def test_gauge_check_bar_and_circle_are_physical_size():
    root = ET.fromstring(figures.render({'gen': 'gauge', 'diameters': [30]}))
    circle = root.find('circle')
    assert float(circle.attrib['r']) == pytest.approx(15 * 96 / 25.4, abs=0.05)
    bar = next(line for line in root.findall('line') if line.attrib['y1'] == line.attrib['y2'])
    assert float(bar.attrib['x2']) - float(bar.attrib['x1']) == pytest.approx(50 * 96 / 25.4, abs=0.1)
    assert 'print at 100%' in ''.join(root.itertext())


def test_generated_gallery_matches_catalog():
    for name, spec in CATALOG.items():
        expected = figures.render(spec).replace('<svg ', '<svg xmlns="http://www.w3.org/2000/svg" ', 1)
        assert (ROOT / f'docs/assets/figures/{name}.svg').read_text() == expected


def test_gallery_files_have_namespace_for_standalone_image_use():
    for name in CATALOG:
        root = ET.parse(ROOT / f'docs/assets/figures/{name}.svg').getroot()
        assert root.tag == '{http://www.w3.org/2000/svg}svg'
