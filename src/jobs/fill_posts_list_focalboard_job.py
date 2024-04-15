import datetime
import logging
import time
from typing import Callable, List

from ..app_context import AppContext
from ..consts import TrelloCardColor, TrelloListAlias
from ..focalboard.focalboard_client import FocalboardClient
from ..sheets.sheets_objects import RegistryPost
from ..strings import load
from ..tg.sender import pretty_send
from ..trello.trello_client import TrelloClient
from .base_job import BaseJob
from .utils import check_trello_card, format_errors

logger = logging.getLogger(__name__)


class FillPostsListFocalboardJob(BaseJob):
    @staticmethod
    def _execute(
        app_context: AppContext,
        send: Callable[[str], None],
        called_from_handler=False,
    ):
        errors = {}
        registry_posts = []
        all_rubrics = app_context.db_client.get_rubrics()
        board_id = app_context.config_manager.get_focalboard_config().get("board_id")

        registry_posts += FillPostsListFocalboardJob._retrieve_cards_for_registry(
            focalboard_client=app_context.focalboard_client,
            trello_client=app_context.trello_client,
            list_aliases=(TrelloListAlias.PROOFREADING, TrelloListAlias.DONE),
            all_rubrics=all_rubrics,
            errors=errors,
            show_due=True,
            strict_archive_rules=True,
            board_id=board_id,
        )

        if len(errors) == 0:
            posts_added = app_context.sheets_client.update_posts_registry(
                registry_posts
            )
            if len(posts_added) == 0:
                paragraphs = [load("fill_posts_list_job__unchanged")]
            else:
                paragraphs = [load("fill_posts_list_job__success")] + [
                    "\n".join(
                        f"{index + 1}) {post_name}"
                        for index, post_name in enumerate(posts_added)
                    )
                ]
        else:
            paragraphs = format_errors(errors)

        pretty_send(paragraphs, send)

    @staticmethod
    def _retrieve_cards_for_registry(
        focalboard_client: FocalboardClient,
        trello_client: TrelloClient,
        list_aliases: List[str],
        errors: dict,
        all_rubrics: List,
        board_id: str,
        show_due=True,
        need_illustrators=True,
        strict_archive_rules=True,
    ) -> List[str]:
        """
        Returns a list of paragraphs that should always go in a single message.
        """
        list_ids = focalboard_client.get_list_id_from_aliases(list_aliases)
        cards = focalboard_client.get_cards(list_ids, board_id)
        if show_due:
            cards.sort(key=lambda card: card.due or datetime.datetime.min)
        parse_failure_counter = 0

        registry_posts = []

        for card in cards:
            label_names = [label.name for label in card.labels]
            is_main_post = load("common_trello_label__main_post") in label_names
            is_archive_post = load("common_trello_label__archive") in label_names

            if not card:
                parse_failure_counter += 1
                continue

            card_fields = focalboard_client.get_fields(card.id)

            card_is_ok = check_trello_card(
                card,
                errors,
                is_bad_title=(
                    card_fields.title is None
                    and card.lst.id
                    != trello_client.lists_config[TrelloListAlias.EDITED_NEXT_WEEK]
                ),
                is_bad_google_doc=card_fields.google_doc is None,
                is_bad_authors=len(card_fields.authors) == 0,
                is_bad_editors=len(card_fields.editors) == 0,
                is_bad_cover=card_fields.cover is None and not is_archive_post,
                is_bad_illustrators=(
                    len(card_fields.illustrators) == 0
                    and need_illustrators
                    and not is_archive_post
                ),
                is_bad_due_date=card.due is None and show_due,
                is_bad_label_names=len(
                    [
                        label
                        for label in card.labels
                        if label.color != TrelloCardColor.BLACK
                    ]
                )
                == 0,
            )

            if not card_is_ok:
                continue

            registry_posts.append(
                RegistryPost(
                    card,
                    card_fields,
                    is_main_post,
                    is_archive_post,
                    all_rubrics,
                )
            )

        if parse_failure_counter > 0:
            logger.error(f"Unparsed cards encountered: {parse_failure_counter}")
        return registry_posts
