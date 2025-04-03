from tortoise import fields, models


class Character(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100)
    description = fields.TextField()
    personality = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)
    user_id = fields.CharField(
        max_length=100
    )  # You can link this to a proper user system later

    class Meta:
        table = "characters"


class ChatMessage(models.Model):
    id = fields.IntField(pk=True)
    character = fields.ForeignKeyField("models.Character", related_name="messages")
    content = fields.TextField()
    is_user = fields.BooleanField()  # True if message is from user, False if from AI
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "chat_messages"
