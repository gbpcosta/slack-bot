import os
import sys
from slackclient import SlackClient


class SlackBot:
    def __init__(self, token=None, user_name=None, channel_name=None):
        try:
            if token is None:
                self.token = os.environ["SLACK_BOT_TOKEN"]
            else:
                self.token = token
        except KeyError as e:
            print("SLACK_BOT_TOKEN enviorement variable needs to defined "
                  "or the token has to be passed as a parameter.")
            sys.exit()

        self.sc = SlackClient(self.token)
        self.user_name = user_name
        self.user_id = None
        if user_name is not None:
            self.set_user_id()

        self.channel_name = channel_name
        self.channel_id = None
        if channel_name is not None:
            self.set_channel_id()
            # self.join_channel(self.channel_id)

    def eval_error(self, ret):
        f_name, ret = ret
        if not ret['ok']:
            print("[*] ERROR in %s: %s" % (f_name, ret['error']))
            return -1
        return 0

    def get_user_id(self, user_name=None):
        assert user_name is not None or self.user_name is not None

        if user_name is None but self.user_name is not None:
            user_name = self.user_name

        users_list = self.get_users_list()
        if users_list['ok']:
            user_id = list(filter(
                lambda user: user['name'] == user_name,
                users_list['members']))[0]['id']
        else:
            print('Error getting users list. '
                  'Setting user id to None.')
            user_id = None

        return user_id

    def set_user_id(self):
        self.user_id = self.get_user_id()
        if self.user_id is None:
            print('Error getting user id. '
                  'Setting user name to None.')
            self.user_name = None

    def get_channel_id(self, channel_name=None):
        assert channel_name is not None or self.channel_name is not None

        if channel_name is None and self.channel_name is not None:
            channel_name = self.channel_name

        channels_list = self.get_channels_list()
        if channels_list['ok']:
            channel_id = list(filter(
                lambda channel: channel['name'] == channel_name,
                channels_list['channels']))[0]['id']
        else:
            print('Error getting channels list. '
                  'Setting channel id to None.')
            channel_id = None

        return channel_id

    def set_channel_id(self):
        self.channel_id = self.get_channel_id()
        if self.channel_id is None:
            print('Error getting channel id. '
                  'Setting channel name to None.')
            self.channel_name = None

    def send_message(self, text, channel_id=None,
                     ephemeral=False, user_id=None):
        if channel_id is None and self.channel_id is not None:
            channel_id = self.channel_id
        if user_id is None and self.user_id is not None:
            user_id = self.user_id

        if not ephemeral:
            self.eval_error(
                ("send_message",
                 self.sc.api_call("chat.postMessage",
                                  channel=channel_id,
                                  text=text))
                )
        else:
            assert user_id is not None

            self.eval_error(
                ("send_message",
                 self.sc.api_call("chat.postEphemeral",
                                  channel=channel_id,
                                  text=text,
                                  user=user_id))
                )

    def send_file(self, filepath, title=None, channel_id=None):
        if channel_id is None and self.channel_id is not None:
            channel_id = self.channel_id

        with open(filepath, 'rb') as file:
            self.eval_error(
                ("send_file",
                 self.sc.api_call('files.upload', channels=channel_id,
                                  filename=os.path.split(filepath)[-1],
                                  as_user=True, file=file, title=title))
                )

    def send_dm(self, text, user_name=None):
        assert user_name is not None or self.user_name is not None

        if user_name is None and self.user_name is not None:
            user_name = self.user_name
            user_id = self.user_id
        else:
            user_id = self.get_user_id(user_name)

        open_im = self.sc.api_call("im.open", user=user_id)

        if self.eval_error(("send_dm", open_im)):
            channel_id = open_im['channel']['id']

            self.eval_error(
                ("send_dm_message",
                 self.sc.api_call("chat.postEphemeral",
                                  channel=channel_id,
                                  text=text))
                )

    def create_channel(self, channel_name, is_private=False):
        self.eval_error(
            ("create_channel",
             self.sc.api_call("conversations.create",
                              name=channel_name,
                              is_private=is_private))
            )

    def join_channel(self, channel_id):
        self.eval_error(
            ("join_channel",
             self.sc.api_call("channels.join",
                              channel=channel_id))
            )

    def leave_channel(self, channel_id):
        self.eval_error(
            ("leave_channel",
             self.sc.api_call("channels.leave",
                              channel=channel_id))
            )

    def get_channels_list(self, exclude_archived=None):
        channels_list = self.sc.api_call("channels.list",
                                         exclude_archived)

        if self.eval_error(("get_channels_list", channels_list)):
            return None
        return channels_list

    def get_users_list(self):
        users_list = self.sc.api_call("users.list")

        if self.eval_error(("get_users_list", users_list)):
            return None
        return users_list

    def get_channel_info(self, channel_id):
        info = self.sc.api_call("channels.info",
                                channel=channel_id)

        if self.eval_error(("get_channel_info", info)):
            return None
        return info

    def open_conversation(self, users_list):
        self.eval_error(
            ("open_conversation",
             self.sc.api_call("conversations.open",
                              users=users_list))
            )
