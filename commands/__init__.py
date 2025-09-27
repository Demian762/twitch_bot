from .basic_commands import BasicCommands
from .games_commands import GameCommands
from .points_commands import PointsCommands
from .drink_commands import DrinkCommands
from .youtube_commands import YoutubeCommands
from .utility_commands import UtilityCommands
from .minigames_commands import MinigamesCommands
from .info_commands import InfoCommands
from .trivia_commands import TriviaCommands
from .insults_commands import InsultsCommands
from .extra_points_commands import ExtraPointsCommands
from .interaction_commands import InteractionCommands

COGS = [
    BasicCommands,
    GameCommands,
    PointsCommands,
    DrinkCommands,
    YoutubeCommands,
    UtilityCommands,
    MinigamesCommands,
    InfoCommands,
    TriviaCommands,
    InsultsCommands,
    ExtraPointsCommands,
    InteractionCommands
]
