from rest_framework.routers import DefaultRouter
from .views import CallLogViewSet, MissedCallQueueViewSet

router = DefaultRouter()
router.register(r'queue', MissedCallQueueViewSet, basename='missed-call-queue')
router.register(r'', CallLogViewSet, basename='call')

urlpatterns = router.urls
