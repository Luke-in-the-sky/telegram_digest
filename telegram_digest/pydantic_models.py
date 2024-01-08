from pydantic import BaseModel
from typing import Optional
import telethon

class Message(BaseModel):
    sender_name: str
    media: Optional[str]
    text: Optional[str]
    reply_to_msg_id: Optional[int] = None
    reply_to_msg: Optional[str] = None

    @classmethod
    def from_telethon_message(cls, message: telethon.tl.patched.Message):
        # Extract sender's name
        sender_name = message.sender.first_name

        # Check if this is a reply to some other message
        reply_to_msg_id, reply_to_msg = None, None
        if message.reply_to:
            reply_to_msg_id = message.reply_to.reply_to_msg_id

        # Determine the type of media attached
        if message.media:
            # Get the class name of the media
            media_class_name = message.media.__class__.__name__
            # Extract the type of media and remove 'MessageMedia'
            media_type = media_class_name.split('.')[-1].replace('MessageMedia', '').strip()
        else:
            media_type = None

        # Extract message text
        message_text = message.message
        if message_text and len(message_text.strip()) < 1:
            message_text = None

        return cls(sender_name=sender_name, media=media_type, text=message_text,
                   reply_to_msg_id=reply_to_msg_id, reply_to_msg=reply_to_msg
                   )
    
    def _set_reply_to_msg(self, reply_to_msg_txt: str = None):
        # Format the `reply`
        if reply_to_msg_txt:
          if len(reply_to_msg_txt) > 50: 
             reply_to_msg_txt = reply_to_msg_txt[:47] + '...'
          self.reply_to_msg = f'<Reply to `{reply_to_msg_txt}`>'

        return self


    def to_str(self):
        # Format the output
        return ' '.join(x for x in [
            f'<Reply to `{self.reply_to_msg}`>' if self.reply_to_msg else None,
            f'[{self.sender_name}]' if self.sender_name else None,
            f'<{self.media}>' if self.media else None,
            self.text
            ] if x is not None)