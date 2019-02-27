#!/usr/bin/env python3

import os
import sys
import subprocess

from config import Config


def main(config_path='io_args.yml'):
    try:
        cfg = Config(config_path).load()

        lang_pair = '{}-{}'.format(cfg['source_language'], cfg['target_language'])
        lang_pair_work_directory = os.path.join(cfg['work_directory'], lang_pair)

        if not os.path.exists(lang_pair_work_directory):
            os.makedirs(lang_pair_work_directory)

        for entry in os.scandir(cfg['preprocessed_source_data_directory']):
            if not entry.name.endswith('_{}.snt'.format(cfg['source_language'])):
                continue

            title = entry.name.rsplit('_', 1)[0]
            target_filepath = '{}_{}.snt'.format(entry.path.rsplit('_', 1)[0], cfg['target_language'])

            if not os.path.exists(target_filepath):
                continue

            p1 = subprocess.Popen(['java',
                                   '-cp',
                                   os.path.join(os.path.join(cfg['maligna']['root'], 'lib'), '*'),
                                   cfg['maligna']['main_class'],
                                   'parse',
                                   '-c',
                                   'txt',
                                   entry.path,
                                   target_filepath],
                                  stdout=subprocess.PIPE,
                                  shell=False)

            p2 = subprocess.Popen(['java',
                                   '-cp',
                                   os.path.join(os.path.join(cfg['maligna']['root'], 'lib'), '*'),
                                   cfg['maligna']['main_class'],
                                   'modify',
                                   '-c',
                                   'split-sentence'],
                                  stdin=p1.stdout,
                                  stdout=subprocess.PIPE,
                                  shell=False)

            p1.stdout.close()

            p3 = subprocess.Popen(['java',
                                   '-cp',
                                   os.path.join(os.path.join(cfg['maligna']['root'], 'lib'), '*'),
                                   cfg['maligna']['main_class'],
                                   'modify',
                                   '-c',
                                   'trim'],
                                  stdin=p2.stdout,
                                  stdout=subprocess.PIPE,
                                  shell=False)

            p2.stdout.close()

            p4 = subprocess.Popen(['java',
                                   '-cp',
                                   os.path.join(os.path.join(cfg['maligna']['root'], 'lib'), '*'),
                                   cfg['maligna']['main_class'],
                                   'align',
                                   '-c',
                                   'viterbi',
                                   '-a',
                                   'normal',
                                   '-n',
                                   'char',
                                   '-s',
                                   'iterative-band'],
                                  stdin=p3.stdout,
                                  stdout=subprocess.PIPE,
                                  shell=False)

            p3.stdout.close()

            p5 = subprocess.Popen(['java',
                                   '-cp',
                                   os.path.join(os.path.join(cfg['maligna']['root'], 'lib'), '*'),
                                   cfg['maligna']['main_class'],
                                   'select',
                                   '-c',
                                   'one-to-one'],
                                  stdin=p4.stdout,
                                  stdout=subprocess.PIPE,
                                  shell=False)

            p4.stdout.close()

            p6 = subprocess.Popen(['java',
                                   '-cp',
                                   os.path.join(os.path.join(cfg['maligna']['root'], 'lib'), '*'),
                                   cfg['maligna']['main_class'],
                                   'format',
                                   '-c',
                                   'txt',
                                   os.path.join(lang_pair_work_directory,
                                                '{}_{}.snt.aligned'.format(title, cfg['source_language'])),
                                   os.path.join(lang_pair_work_directory,
                                                '{}_{}.snt.aligned'.format(title, cfg['target_language']))],
                                  stdin=p5.stdout)
            p5.stdout.close()

            p1.wait()
            p2.wait()
            p3.wait()
            p4.wait()
            p5.wait()

    except Exception as ex:
        sys.stderr.write(repr(ex))
        return 1


if __name__ == '__main__':
    sys.exit(main(*sys.argv[1:]))
