from accounts.models import User
from accounts.serializers import UserSerializer
u = User.objects.filter(id=2)
s = UserSerializer(u[0])
print(s.data)
