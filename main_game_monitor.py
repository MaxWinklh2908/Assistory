from argparse import ArgumentParser
from typing import Callable

from assistory.utils import game_file_scanner
import main_game_stats

def get_callback_function(
    print_problems,
    print_actors,
    print_unlocking,
    print_progress,
    print_production,
    print_paused,
) -> Callable:
    
    def stats_callback(save_file_path: str):
        main_game_stats.main(
            save_file_path,
            print_problems_=print_problems,
            print_actors_=print_actors,
            print_unlocking_=print_unlocking,
            print_progress_=print_progress,
            print_production_=print_production,
            print_paused_=print_paused,
        )

    return stats_callback


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('directory_to_monitor',
                        help='Directory path to monitor for changed or new files')
    parser.add_argument('--print-problems', required=False, action='store_true',
                        help='List all detected problems of factories')
    parser.add_argument('--print-actors', required=False, action='store_true',
                        help='List of all actors')
    parser.add_argument('--print-unlocking', required=False, action='store_true',
                        help='List unlocked recipes and factory buildings')
    parser.add_argument('--print-progress', required=False, action='store_true',
                        help='Show progress of milestone and game phase and project goal time')
    parser.add_argument('--print-production', required=False, action='store_true',
                        help='Summarize production statistics')
    parser.add_argument('--print-paused', required=False, action='store_true',
                        help='List paused factories')
    args = parser.parse_args()

    stats_callback = get_callback_function(
            print_problems=args.print_problems,
            print_actors=args.print_actors,
            print_unlocking=args.print_unlocking,
            print_progress=args.print_progress,
            print_production=args.print_production,
            print_paused=args.print_paused,
    )

    game_file_scanner.monitor_directory(args.directory_to_monitor, stats_callback)
