from .. import discover
from unittest.mock import patch, Mock

@patch('requests.get')
def test_ubuntu_handler(m_requests_get):
    h = discover.UbuntuHandler()
    assert 'focal' == h.get_release('20.04')
    assert '18.04' == h.get_version('bionic')
    m_request = Mock()
    m_request.content = (
        b"<html>\n<body>\n<div>\n<div>\n<pre><hr>\n"
        b'<a href="/releases/">Parent Directory</a>\n'
        b'<a href="release-20241216/">release-20241216/</a>\n'
        b'<a href="release-20250109/">release-20250109/</a>\n'
        b'<a href="release/">release/</a>\n'
        b"<hr></pre>\n"
        b"</div></div></body></html>\n")
    m_requests_get.return_value = m_request
    assert ('20250109','release') == h.get_latest_release_serial('focal')

@patch('downburst.discover.UbuntuHandler.get_latest_release_serial')
def test_get(m_get_latest_release_serial):
    m_get_latest_release_serial.return_value = ('20230420', 'release')
    checksum = 'cd824b19795e8a6b9ae993b0b5157de0275e952a7a9e8b9717ca07acec22f51b'
    res = discover.get('ubuntu', '20.04', 'x86_64')
    assert checksum == res['checksum']

