from tests.conftest import login, make_user


def test_admin_endpoints_reject_normal_users(client, user_headers):
    for path in ("/api/v1/admin/users", "/api/v1/admin/audit-logs"):
        assert client.get(path, headers=user_headers).status_code == 403
    assert client.get("/api/v1/admin/users").status_code == 401


def test_moderator_cannot_manage_users_but_can_see_sources(client, app):
    make_user("mod@example.com", role="moderator")
    h = login(client, "mod@example.com")
    assert client.get("/api/v1/admin/users", headers=h).status_code == 403
    assert client.get("/api/v1/admin/data-sources", headers=h).status_code == 200


def test_admin_changes_role_and_it_is_audited(client, admin_headers, app):
    target = make_user("t@example.com")
    r = client.patch(f"/api/v1/admin/users/{target.id}", headers=admin_headers, json={"role": "moderator"})
    assert r.status_code == 200 and r.get_json()["role"] == "moderator"
    logs = client.get("/api/v1/admin/audit-logs?action=admin.user_update", headers=admin_headers).get_json()
    assert logs["total"] == 1 and logs["items"][0]["details"]["after"] == {"role": "moderator"}


def test_admin_cannot_change_self_or_use_invalid_role(client, admin_headers, app):
    me = client.get("/api/v1/users/me", headers=admin_headers).get_json()
    assert client.patch(f"/api/v1/admin/users/{me['id']}", headers=admin_headers,
                        json={"status": "suspended"}).status_code == 409
    other = make_user("t@example.com")
    assert client.patch(f"/api/v1/admin/users/{other.id}", headers=admin_headers,
                        json={"role": "superuser"}).status_code == 422


def test_user_list_filters_and_paginates(client, admin_headers, app):
    for i in range(5):
        make_user(f"u{i}@example.com")
    r = client.get("/api/v1/admin/users?q=u1&per_page=2", headers=admin_headers).get_json()
    assert r["total"] == 1
    r = client.get("/api/v1/admin/users?per_page=2&page=2", headers=admin_headers).get_json()
    assert len(r["items"]) == 2 and r["pages"] == 3
