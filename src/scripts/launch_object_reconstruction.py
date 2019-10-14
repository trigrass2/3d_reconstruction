import json
import argparse
import time, datetime
import sys
import os
from pprint import pprint

sys.path.append(".")
sys.path.append("../")

from utils.file import check_folder_structure, get_project_root_dir
from utils.object_reconstruction_config import get_config, specify_config_pathes
from utils.logs import log_stats, make_stats

from filter_outliers_raw_images import launch_filter_raw_images
from texture_colormap_optimization import run_colormap_optimisarion

PROJECT_NAME = "object_3d_reconstruction"
DEFAULT_CONFIFG_FILENAME = 'cfg/reconstruction/default/main.json'


if __name__ == "__main__":

    stats = make_stats()
    parser = argparse.ArgumentParser(description="Object reconstruction pipeline launcher")
    parser.add_argument("--config", help="path to the config file")
    args = parser.parse_args()
    config_filename = DEFAULT_CONFIFG_FILENAME
    if args.config is not None:
        config_filename = args.config

    project_root = get_project_root_dir(os.getcwd(), PROJECT_NAME)

    condig_file_fullpath = config_filename
    if PROJECT_NAME not in config_filename and not os.path.isabs(condig_file_fullpath):
        condig_file_fullpath = os.path.join(project_root, config_filename)

    config = get_config(condig_file_fullpath)
    config['project_root'] = project_root
    stats['config']['main'] = config

    if config['preprocessing_images']:
        preprocessing_cfg_fname = os.path.join( config['project_root'],
                                                config['preprocessing_config'])
        preprocessing_cfg = get_config(preprocessing_cfg_fname)
        stats['config']['preprocessing'] = preprocessing_cfg

        preprocessing_cfg = specify_config_pathes(subconfig=preprocessing_cfg,
                              main_cfg=config)

        stage_start_time = time.time()
        launch_filter_raw_images(preprocessing_cfg)
        stats['exec_time']['preprocessing_images'] = time.time() - stage_start_time


    if config['reconstruction']:
        reconstruction_args = config['reconstruction_args']
        stats['config']['reconstrunction'] = reconstruction_args
        reconstruction_cfg = get_config(os.path.join( config['project_root'], reconstruction_args['config']))
        stats['config']['reconstrunction']['parameters'] = reconstruction_cfg

        reconstruction_runner_filename = reconstruction_args['runfile']
        if not os.path.isabs(reconstruction_runner_filename):
            reconstruction_runner_filename = os.path.join(project_root, reconstruction_runner_filename)

        runfile_dir, runfile_name = os.path.split(reconstruction_runner_filename)
        sys.path.append(runfile_dir)
        os.chdir(runfile_dir)

        specified_config_filename = os.path.join(
            config['project_root'],
            os.path.join(os.path.dirname(reconstruction_args['config']),
                         'reconstruction.json')
            )

        specify_config_pathes( subconfig=reconstruction_cfg,
                               main_cfg=config,
                               updated_config_filename=specified_config_filename)

        for stage_name in ['make', 'register', 'refine', 'integrate']:
            if reconstruction_args[stage_name]:
                reconstruction_steps_flags = ' --{} '.format(stage_name)
                if (reconstruction_args['debug_mode']):
                    reconstruction_steps_flags += " --debug_mode "
                exec_line = " ".join(["python",
                                      runfile_name,
                                      specified_config_filename,
                                      reconstruction_steps_flags
                                      ])
                stage_start_time = time.time()
                os.system(exec_line)
                stats['exec_time']['reconstruction'][stage_name] = time.time() - stage_start_time


    if config['optimize_colormap']:
        optimize_colormap_config_filename = os.path.join(config['project_root'],
                                               config['optimize_colormap_config'])
        optimize_colormap_config = get_config(optimize_colormap_config_filename)
        stats['config']['colormap_optimization'] = optimize_colormap_config

        optimize_colormap_config = specify_config_pathes(subconfig=optimize_colormap_config,
                                                         main_cfg=config)

        stage_start_time = time.time()
        run_colormap_optimisarion(optimize_colormap_config)
        stats['exec_time']['colormap_optimization'] = time.time() - stage_start_time


    log_stats(stats, config)





