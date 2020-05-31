import logging
import requests


from . import trello_objects as objects
from ..consts import TrelloListAlias, TrelloCustomFieldTypeAlias
from ..utils.singleton import Singleton


logger = logging.getLogger(__name__)

BASE_URL = 'https://api.trello.com/1/'


class TrelloClient(Singleton):
    def __init__(self, config=None):
        if self.was_initialized():
            return

        self._trello_config = config
        self._update_from_config()
        logger.info('TrelloClient successfully initialized')

    def get_board(self, board_id=None):
        _, data = self._make_request(f'boards/{board_id or self.board_id}')
        return objects.TrelloBoard.from_dict(data)

    def get_board_labels(self, board_id=None):
        _, data = self._make_request(f'boards/{board_id or self.board_id}/labels')
        labels = [
            objects.TrelloBoardLabel.from_dict(label) for label in data
        ]
        logger.debug(f'get_board_labels: {labels}')
        return labels

    def get_lists(self, board_id=None):
        _, data = self._make_request(f'boards/{board_id or self.board_id}/lists')
        lists = [
            objects.TrelloList.from_dict(trello_list) for trello_list in data
        ]
        logger.debug(f'get_lists: {lists}')
        return lists

    def get_cards(self, list_ids=None, board_id=None):
        if list_ids is not None and len(list_ids) == 1:
            _, data = self._make_request(f'lists/{list_ids[0]}/cards')
        else:
            _, data = self._make_request(f'boards/{board_id or self.board_id}/cards')
            if list_ids:
                data = [
                    card_dict for card_dict in data
                    if card_dict['idList'] in list_ids
                ]
        cards = []
        # TODO: move this to app state
        members = self.get_members()
        lists = self.get_lists()
        for card_dict in data:
            card = objects.TrelloCard.from_dict(card_dict)
            # TODO: move this to app state
            for trello_list in lists:
                if trello_list.id == card_dict['idList']:
                    card.lst = trello_list
                    break
            else:
                logger.error(f"List name not found for {card}")
            # TODO: move this to app state
            if len(card_dict['idMembers']) > 0:
                for member in members:
                    if member.id in card_dict['idMembers']:
                        card.members.append(member)
                if len(card.members) == 0:
                    logger.error(f"Member username not found for {card}")
            cards.append(card)
        logger.debug(f'get_cards: {cards}')
        return cards

    def get_board_custom_field_types(self, board_id=None):
        _, data = self._make_request(f'boards/{board_id or self.board_id}/customFields')
        custom_field_types = [
            objects.TrelloCustomFieldType.from_dict(custom_field_type)
            for custom_field_type in data
        ]
        logger.debug(f'get_board_custom_field_types: {custom_field_types}')
        return custom_field_types

    def get_card_custom_fields(self, card_id):
        _, data = self._make_request(f'cards/{card_id}/customFieldItems')
        custom_fields = [
            objects.TrelloCustomField.from_dict(custom_field) for custom_field in data
        ]
        logger.debug(f'get_card_custom_fields: {custom_fields}')
        return custom_fields

    def get_card_custom_fields_dict(self, card_id):
        custom_fields = self.get_card_custom_fields(card_id)
        custom_fields_dict = {}
        for alias, type_id in self.custom_fields_config.items():
            suitable_fields = [fld for fld in custom_fields if fld.type_id == type_id]
            if len(suitable_fields) > 0:
                custom_fields_dict[alias] = suitable_fields[0]
        return custom_fields_dict

    def get_custom_fields(self, card_id):
        # TODO: think about better naming
        card_fields_dict = self.get_card_custom_fields_dict(card_id)
        card_fields = objects.CardCustomFields(card_id)
        card_fields.authors = (
            card_fields_dict[TrelloCustomFieldTypeAlias.AUTHOR].value.split(',')
            if TrelloCustomFieldTypeAlias.AUTHOR in card_fields_dict else []
        )
        card_fields.editors = (
            card_fields_dict[TrelloCustomFieldTypeAlias.EDITOR].value.split(',')
            if TrelloCustomFieldTypeAlias.EDITOR in card_fields_dict else []
        )
        card_fields.illustrators = (
            card_fields_dict[TrelloCustomFieldTypeAlias.ILLUSTRATOR].value.split(',')
            if TrelloCustomFieldTypeAlias.ILLUSTRATOR in card_fields_dict else []
        )
        card_fields.google_doc = (
            card_fields_dict[TrelloCustomFieldTypeAlias.GOOGLE_DOC].value
            if TrelloCustomFieldTypeAlias.GOOGLE_DOC in card_fields_dict else None
        )
        card_fields.title = (
            card_fields_dict[TrelloCustomFieldTypeAlias.TITLE].value
            if TrelloCustomFieldTypeAlias.TITLE in card_fields_dict else None
        )
        return card_fields

    def get_action_create_card(self, card_id):
        _, data = self._make_request(
            f'cards/{card_id}/actions', payload={'filter': 'createCard'}
        )
        card_actions = [
            objects.TrelloActionCreateCard.from_dict(action)
            for action in data
        ]
        logger.debug(f'get_action_create_card: {card_actions}')
        return card_actions

    def get_action_create_cards(self, card_ids):
        card_actions = {}
        for card_id in card_ids:
            card_actions[card_id] = self.get_action_create_card(card_id)
        return card_actions

    def get_action_update_card(self, card_id):
        _, data = self._make_request(
            f'cards/{card_id}/actions', payload={'filter': 'updateCard'}
        )
        card_actions = [
            objects.TrelloActionUpdateCard.from_dict(action)
            for action in data
        ]
        logger.debug(f'get_action_update_card: {card_actions}')
        return card_actions

    def get_action_update_cards(self, card_ids):
        card_actions = {}
        for card_id in card_ids:
            card_actions[card_id] = self.get_action_update_card(card_id)
        return card_actions

    def get_members(self, board_id=None):
        _, data = self._make_request(f'boards/{board_id or self.board_id}/members')
        members = [objects.TrelloMember.from_dict(member) for member in data]
        logger.debug(f'get_members: {members}')
        return members

    def update_config(self, new_trello_config):
        """To be called after config automatic update"""
        self._trello_config = new_trello_config
        self._update_from_config()

    def _update_from_config(self):
        """Update attributes according to current self._trello_config"""
        self.api_key = self._trello_config['api_key']
        self.token = self._trello_config['token']
        self.board_id = self._trello_config['board_id']
        self.default_payload = {
            'key': self.api_key,
            'token': self.token,
        }
        lists = self.get_lists()
        self.lists_config = self._fill_id_alias_map(lists, TrelloListAlias)
        custom_field_types = self.get_board_custom_field_types()
        self.custom_fields_config = self._fill_id_alias_map(
            custom_field_types, TrelloCustomFieldTypeAlias
        )

    def _fill_id_alias_map(self, items, item_enum):
        result = {}
        for alias in item_enum:
            suitable_items = [item for item in items if item.name.startswith(alias.value)]
            if len(suitable_items) != 1:
                raise ValueError(f'Enum {item_enum.__name__} name {alias.value} is ambiguous!')
            result[alias] = suitable_items[0].id
        return result

    def _make_request(self, uri, payload={}):
        payload.update(self.default_payload)
        response = requests.get(
            f'{BASE_URL}{uri}',
            params=payload,
        )
        logger.debug(f'{response.url}')
        return response.status_code, response.json()
