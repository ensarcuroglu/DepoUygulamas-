"""
Parametrize rol erişim matrisi — tüm endpoint grupları.

Her sınıf bir erişim politikasını temsil eder; çift parametrize ile
endpoint × rol kombinasyonları otomatik üretilir:

  AdminOnly     — admin: 200, diğerleri: 401/403
  AdminLojistik — admin+lojistik: 200, depocu: 403, anonim: 401
  HerkesErisir  — tüm giriş yapmışlar: 200, anonim: 401
"""

import pytest

pytestmark = pytest.mark.api


def _get_client(request, fixture_name: str):
    """request.getfixturevalue yardımcısı — fixture adından client döndürür."""
    return request.getfixturevalue(fixture_name)


class TestAdminOnlyEndpointler:
    """Sadece admin erişebilen GET endpoint'leri."""

    @pytest.mark.parametrize("endpoint", [
        "/api/kategoriler/",
        "/api/markalar/",
        "/api/kullanicilar/",
    ])
    @pytest.mark.parametrize("client_fixture,beklenen", [
        ("client",          401),
        ("depocu_client",   403),
        ("lojistik_client", 403),
        ("admin_client",    200),
    ])
    def test_admin_only_get(self, endpoint, client_fixture, beklenen, request):
        client = _get_client(request, client_fixture)
        assert client.get(endpoint).status_code == beklenen


class TestAdminLojistikEndpointler:
    """Admin ve lojistik erişebilen GET endpoint'leri — depocu yasak."""

    @pytest.mark.parametrize("endpoint", [
        "/api/depolar/",
        "/api/siparisler/",
        "/api/sevkiyat-planlama/",
    ])
    @pytest.mark.parametrize("client_fixture,beklenen", [
        ("client",          401),
        ("depocu_client",   403),
        ("lojistik_client", 200),
        ("admin_client",    200),
    ])
    def test_admin_lojistik_get(self, endpoint, client_fixture, beklenen, request):
        client = _get_client(request, client_fixture)
        assert client.get(endpoint).status_code == beklenen


class TestHerkesErisisEndpointler:
    """Tüm giriş yapmış kullanıcıların erişebildiği GET endpoint'leri."""

    @pytest.mark.parametrize("endpoint", [
        "/api/raflar/",
        "/api/lotlar/",
        "/api/stok-sayimlar",
    ])
    @pytest.mark.parametrize("client_fixture,beklenen", [
        ("client",          401),
        ("depocu_client",   200),
        ("lojistik_client", 200),
        ("admin_client",    200),
    ])
    def test_herkesim_get(self, endpoint, client_fixture, beklenen, request):
        client = _get_client(request, client_fixture)
        assert client.get(endpoint).status_code == beklenen
