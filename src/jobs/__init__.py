"""
A module for business logic-containing regular jobs.
Jobs should use corresponding client objects to interact with
Trello, Spreadsheets or Telegram API.
Jobs can be ran from scheduler or from anywhere else for a one-off action.
"""


from .config_updater_job import ConfigUpdaterJob
from .create_folders_for_illustrators_job import CreateFoldersForIllustratorsJob
from .db_fetch_authors_sheet_job import DBFetchAuthorsSheetJob
from .db_fetch_curators_sheet_job import DBFetchCuratorsSheetJob
from .db_fetch_strings_sheet_job import DBFetchStringsSheetJob
from .db_fetch_team_sheet_job import DBFetchTeamSheetJob
from .editorial_report_job import EditorialReportJob
from .fb_analytics_report_job import FBAnalyticsReportJob
from .fill_posts_list_job import FillPostsListJob
from .hr_acquisition_job import HRAcquisitionJob
from .hr_check_chat_consistency_job import HRCheckChatConsistencyJob
from .hr_check_chat_consistency_frozen_job import HRCheckChatConsistencyFrozenJob
from .hr_check_trello_consistency_job import HRCheckTrelloConsistencyJob
from .hr_check_trello_consistency_frozen_job import HRCheckTrelloConsistencyFrozenJob
from .hr_get_members_without_telegram_job import HRGetMembersWithoutTelegramJob
from .hr_status_job import HRStatusJob
from .ig_analytics_report_job import IGAnalyticsReportJob
from .illustrative_report_members_job import IllustrativeReportMembersJob
from .illustrative_report_columns_job import IllustrativeReportColumnsJob
from .main_stats_job import MainStatsJob
from .publication_plans_job import PublicationPlansJob
from .sample_job import SampleJob
from .site_health_check_job import SiteHealthCheckJob
from .sheet_report_job import SheetReportJob
from .shrug_job import ShrugJob
from .send_reminders_job import SendRemindersJob
from .tg_analytics_report_job import TgAnalyticsReportJob
from .trello_board_state_job import TrelloBoardStateJob
from .trello_get_articles_arts_job import TrelloGetArticlesArtsJob
from .trello_get_articles_rubric_job import TrelloGetArticlesRubricJob
from .trello_board_state_notifications_job import TrelloBoardStateNotificationsJob
from .vk_analytics_report_job import VkAnalyticsReportJob
