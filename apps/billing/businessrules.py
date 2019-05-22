# -*- coding: utf-8 -*-
from .models import Plan


class ChangePlan(object):
    @staticmethod
    def allowed_plans(current_plan_id):
        """
        Returns the allowed plans for selection in the change plan view,
        depending on the database config and the user's current plan.
        :param current_plan_id: pk of the user's current plan (or None if no plan registered for the user)
        :return: list of IDs (pk values) of the selectable plans
        """
        plans = Plan.objects.filter(available=True)
        if current_plan_id is not None:
            plans = plans.exclude(pk=current_plan_id)
        return plans.values_list("pk", flat=True)
