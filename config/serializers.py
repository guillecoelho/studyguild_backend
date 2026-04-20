"""Shared serializer mixins.

`BusinessRulesMixin` — funnels model `clean()` errors (Rails
`validate :method_name` equivalents) through DRF so they surface as
422 with `{"errors": [...]}` via the custom exception handler.
"""
from copy import copy

from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers


class BusinessRulesMixin:
    """Run `model.clean()` during serializer validation.

    Builds a transient (unsaved) instance from validated_data, sets
    non-m2m attributes, and invokes `clean()`. Converts any
    `django.core.exceptions.ValidationError` into DRF `ValidationError`.
    """

    def validate(self, attrs):
        attrs = super().validate(attrs)
        model_cls = self.Meta.model
        m2m_names = {f.name for f in model_cls._meta.many_to_many}
        scalar_attrs = {k: v for k, v in attrs.items() if k not in m2m_names}

        if self.instance is not None:
            instance = copy(self.instance)
            for k, v in scalar_attrs.items():
                setattr(instance, k, v)
        else:
            instance = model_cls(**scalar_attrs)

        try:
            instance.clean()
        except DjangoValidationError as exc:
            if hasattr(exc, "message_dict"):
                raise serializers.ValidationError(exc.message_dict)
            raise serializers.ValidationError({"non_field_errors": exc.messages})

        return attrs
