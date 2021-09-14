import logging

from lxml import etree

log = logging.getLogger(__name__)

def lookup_emulator(xml_text, arch):
    """
    Find emulator path for the arch in capabilities xml
    """
    arch_map = {
        'amd64':        'x86_64',
        'x86_64':       'x86_64',
        'i686':         'i686',
    }
    _arch = arch_map.get(arch, None)
    assert _arch
    tree = etree.fromstring(xml_text)
    emulator_xpath = f'/capabilities/guest/arch[@name="{_arch}"]/emulator'
    log.debug(f'Looking for: {emulator_xpath}')
    emulators = tree.xpath(emulator_xpath)
    if emulators:
        return emulators[0].text
    else:
        return None
