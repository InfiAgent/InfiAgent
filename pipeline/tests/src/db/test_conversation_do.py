import unittest
from datetime import datetime

from src.db.conversation_do import ConversationDO, SandboxStatus, ConversationStatus, MessageConf
from src.schemas import RoleType


class TestConversationDO(unittest.TestCase):

    def setUp(self):
        # Sample data for testing with the new fields
        self.sample_data = {
            "conversation_id": "12345",
            "messages": [{"role": "user", "content": "Hello"}],
            "input_files": [{"name": "file1.txt"}],
            "output_files": [{"name": "file2.txt"}],
            "sandbox_id": "sandbox_sample",
            "sandbox_status": "RUNNING",
            "create_time": datetime.utcnow(),
            "update_time": datetime.utcnow(),
            "user": "test_user_v3",
            "model_name": "sample_model",
            "model_conf_path": "path/to/conf",
            "llm_name": "sample_llm",
            "agent_type": "sample_agent",
            "request_id": "request_sample",
            "dead_sandbox_ids": ["dead1", "dead2"],
            "status": "RUNNING"
        }

    def test_init(self):
        conversation = ConversationDO(**self.sample_data)
        self.assertEqual(conversation.conversation_id, "12345")
        self.assertEqual(len(conversation.messages), 1)
        self.assertEqual(conversation.messages[0].role, RoleType.User)
        self.assertEqual(conversation.messages[0].content, "Hello")

    def test_to_dict(self):
        conversation = ConversationDO(**self.sample_data)
        data = conversation.to_dict()
        self.assertEqual(data["conversation_id"], "12345")
        self.assertEqual(data["sandbox_status"], "RUNNING")
        self.assertEqual(len(data["messages"]), 1)
        self.assertEqual(data["messages"][0]["role"], 0)
        self.assertEqual(data["messages"][0]["content"], "Hello")

    def test_from_dict(self):
        data = self.sample_data.copy()
        conversation = ConversationDO.from_dict(data)
        self.assertEqual(conversation.conversation_id, "12345")
        self.assertEqual(len(conversation.messages), 1)
        self.assertEqual(conversation.messages[0].role, RoleType.User)
        self.assertEqual(conversation.messages[0].content, "Hello")

    def test_update(self):
        conversation = ConversationDO(**self.sample_data)
        updated_data = {
            "sandbox_status": "KILLED",
            "user": "updateduser",
            "messages": [{"role": "Agent", "content": "Hi"}]
        }
        conversation.update(updated_data)
        self.assertEqual(conversation.sandbox_status, SandboxStatus.KILLED)
        self.assertEqual(conversation.user, "updateduser")
        self.assertEqual(len(conversation.messages), 1)
        self.assertEqual(conversation.messages[0].role, RoleType.Agent)
        self.assertEqual(conversation.messages[0].content, "Hi")

    def test_invalid_status(self):
        # Testing invalid sandbox_status
        data = self.sample_data.copy()
        data["sandbox_status"] = "INVALID_STATUS"
        conversation = ConversationDO(**data)
        self.assertEqual(conversation.sandbox_status, SandboxStatus.UNKNOWN)

        # Testing invalid conversation status
        data["status"] = "INVALID_STATUS"
        conversation = ConversationDO.from_dict(data)
        self.assertEqual(conversation.status, ConversationStatus.UNKNOWN)

    def test_is_in_running_status(self):
        conversation = ConversationDO(**self.sample_data)
        self.assertTrue(conversation.is_in_running_status())
        conversation.status = ConversationStatus.COMPLETED
        self.assertFalse(conversation.is_in_running_status())

    def test_message_conf(self):
        # Test initialization with a MessageConf object
        conf = MessageConf(temperature=0.9, top_p=0.8, top_k=5)
        conversation = ConversationDO(message_conf=conf, **self.sample_data)
        self.assertEqual(conversation.message_conf.__temperature, 0.9)
        self.assertEqual(conversation.message_conf.__top_p, 0.8)
        self.assertEqual(conversation.message_conf.__top_k, 5)

        # Test initialization with a dictionary
        conf_dict = {"temperature": 0.9, "top_p": 0.8, "top_k": 5}
        conversation = ConversationDO(message_conf=conf_dict, **self.sample_data)
        self.assertEqual(conversation.message_conf.__temperature, 0.9)
        self.assertEqual(conversation.message_conf.__top_p, 0.8)
        self.assertEqual(conversation.message_conf.__top_k, 5)

    def test_to_dict_with_message_conf(self):
        conf = MessageConf(temperature=0.9, top_p=0.8, top_k=5)
        conversation = ConversationDO(message_conf=conf, **self.sample_data)
        data = conversation.to_dict()
        self.assertEqual(data["message_conf"]["temperature"], 0.9)
        self.assertEqual(data["message_conf"]["top_p"], 0.8)
        self.assertEqual(data["message_conf"]["top_k"], 5)

    def test_from_dict_with_message_conf(self):
        data = self.sample_data.copy()
        data["message_conf"] = {"temperature": 0.9, "top_p": 0.8, "top_k": 5}
        conversation = ConversationDO.from_dict(data)
        self.assertEqual(conversation.message_conf.__temperature, 0.9)
        self.assertEqual(conversation.message_conf.__top_p, 0.8)
        self.assertEqual(conversation.message_conf.__top_k, 5)

    def test_update_with_message_conf(self):
        conversation = ConversationDO(**self.sample_data)
        updated_data = {
            "message_conf": {"temperature": 0.9, "top_p": 0.8, "top_k": 5}
        }
        conversation.update(updated_data)
        self.assertEqual(conversation.message_conf.__temperature, 0.9)
        self.assertEqual(conversation.message_conf.__top_p, 0.8)
        self.assertEqual(conversation.message_conf.__top_k, 5)
