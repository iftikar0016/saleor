import graphene
from django.core.exceptions import ValidationError

from .....product import models as product_models
from ....core import ResolveInfo
from ....core.mutations import BaseMutation
from ....core.types import ProductError
from ...types import Product


class RecordProductView(BaseMutation):
    product = graphene.Field(Product, description="The viewed product.")

    class Arguments:
        id = graphene.ID(required=True, description="ID of the viewed product.")
        session_key = graphene.String(
            required=False,
            description="Session key for anonymous users.",
        )

    class Meta:
        description = "Record a product view for recently viewed products."
        error_type_class = ProductError
        error_type_field = "product_errors"

    @classmethod
    def perform_mutation(cls, _root, info: ResolveInfo, /, *, id, session_key=None):
        # Resolve the product instance from the global ID
        product = cls.get_node_or_error(
            info, id, field="id", only_type=Product
        )

        user = info.context.user
        if not user or user.is_anonymous:
            user = None

        if not user and not session_key:
            raise ValidationError(
                {
                    "session_key": ValidationError(
                        "User must be logged in or session_key must be provided.",
                        code="required",
                    )
                }
            )

        # Record the view using the manager
        product_models.RecentlyViewedProduct.objects.record_view(
            product=product,
            user=user,
            session_key=session_key
        )

        return RecordProductView(product=product, errors=[])
