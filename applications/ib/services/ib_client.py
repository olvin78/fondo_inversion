import os
import time
import random
from ib_insync import IB
from django.conf import settings


def get_ib_client():
    ib = IB()
    ib.connect(
        settings.IBKR_HOST,
        settings.IBKR_PORT,
        clientId=settings.IBKR_CLIENT_ID,
        timeout=10,
    )
    return ib
