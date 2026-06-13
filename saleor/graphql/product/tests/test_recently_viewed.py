import graphene
from ....product.models import RecentlyViewedProduct
from ...tests.utils import get_graphql_content

RECORD_VIEW_MUTATION = """
    mutation RecordProductView($id: ID!, $sessionKey: String) {
        recordProductView(id: $id, sessionKey: $sessionKey) {
            product {
                id
                name
            }
            errors {
                field
                message
            }
        }
    }
"""

RECENTLY_VIEWED_QUERY = """
    query GetRecentlyViewedProducts($sessionKey: String, $channel: String) {
        recentlyViewedProducts(sessionKey: $sessionKey, channel: $channel) {
            id
            name
        }
    }
"""


def test_record_product_view_for_user(user_api_client, product):
    # given
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id)
    }

    # when
    response = user_api_client.post_graphql(RECORD_VIEW_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["recordProductView"]
    assert not data["errors"]
    assert data["product"]["id"] == variables["id"]

    # verify in DB
    assert RecentlyViewedProduct.objects.filter(
        user=user_api_client.user, product=product
    ).exists()


def test_record_product_view_for_anonymous(api_client, product):
    # given
    session_key = "test-session-123"
    variables = {
        "id": graphene.Node.to_global_id("Product", product.id),
        "sessionKey": session_key,
    }

    # when
    response = api_client.post_graphql(RECORD_VIEW_MUTATION, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["recordProductView"]
    assert not data["errors"]

    # verify in DB
    assert RecentlyViewedProduct.objects.filter(
        session_key=session_key, product=product
    ).exists()


def test_recently_viewed_products_query_limit_and_order(
    user_api_client, product_list, channel_USD
):
    user = user_api_client.user

    # record views for the products in product_list
    for p in product_list:
        RecentlyViewedProduct.objects.record_view(product=p, user=user)

    # when
    variables = {"channel": channel_USD.slug}
    response = user_api_client.post_graphql(RECENTLY_VIEWED_QUERY, variables)

    # then
    content = get_graphql_content(response)
    data = content["data"]["recentlyViewedProducts"]

    # We should get products in reverse chronological order (newest first)
    expected_names = [p.name for p in reversed(product_list)][:5]
    received_names = [p["name"] for p in data]
    assert len(received_names) <= 5
    assert received_names == expected_names
