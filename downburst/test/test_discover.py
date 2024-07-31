from .. import discover
from unittest.mock import patch, Mock

@patch('requests.get')
def test_ubuntu_handler(m_requests_get):
    h = discover.UbuntuHandler()
    assert 'focal' == h.get_release('20.04')
    assert '18.04' == h.get_version('bionic')
    m_request = Mock()
    m_request.content = (
            b"focal	server	release	20230302\n"
            b"jammy	server	release	20230303\n")
    m_requests_get.return_value = m_request
    assert ('20230302','release') == h.get_serial('focal')

@patch('downburst.discover.UbuntuHandler.get_serial')
def test_get(m_get_serial):
    m_get_serial.return_value = ('20230420', 'release')
    checksum = 'cd824b19795e8a6b9ae993b0b5157de0275e952a7a9e8b9717ca07acec22f51b'
    res = discover.get('ubuntu', '20.04', 'x86_64')
    assert checksum == res['checksum']

