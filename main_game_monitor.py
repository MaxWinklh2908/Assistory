from argparse import ArgumentParser

from assistory.utils import game_file_scanner
import main_game_stats


def stats_callback(save_file_path: str):
    main_game_stats.main(save_file_path)


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('directory_to_monitor', help='Directory path to monitor for changed or new files')
    args = parser.parse_args()

    game_file_scanner.monitor_directory(args.directory_to_monitor, stats_callback)
