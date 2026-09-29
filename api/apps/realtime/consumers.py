from channels.generic.websocket import AsyncJsonWebsocketConsumer

from .notify import GYM_GROUP

UNAUTHORIZED_CLOSE_CODE = 4401


class GroupConsumer(AsyncJsonWebsocketConsumer):
    group_name = None

    def group_for(self, user):
        raise NotImplementedError

    async def connect(self):
        user = self.scope["user"]
        group_name = None
        if user.is_authenticated:
            group_name = self.group_for(user)
        if group_name is None:
            await self.accept()
            await self.close(code=UNAUTHORIZED_CLOSE_CODE)
            return
        self.group_name = group_name
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        if self.group_name is not None:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def send_event(self, event):
        await self.send_json(event["payload"])


class LiveConsumer(GroupConsumer):
    def group_for(self, user):
        if not user.is_runner:
            return None
        return f"live.user.{user.id}"


class GymConsumer(GroupConsumer):
    def group_for(self, user):
        if not user.is_gym_admin:
            return None
        return GYM_GROUP
