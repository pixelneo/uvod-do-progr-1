#!/usr/bin/env python3

import os
import re
import shutil
import yaml
import logging
from collections import defaultdict

class Convertor:
    def __init__(self, out_dir, ignore=None, force=False):
        if os.path.exists(out_dir):
            if force:
                shutil.rmtree(out_dir)
            else:
                raise ValueError("Output directory already exists")
        self.out_dir = out_dir
        os.mkdir(self.out_dir)
        self.ignore = ignore or []


    def _sub(self, dir_, key):
        file = os.path.join(dir_, 'entry.yml')
        if not os.path.exists(file):
            raise ValueError('No entry.yml found in {}'.format(dir_))
        with open(file, 'r') as f:
            data = yaml.safe_load(f)
        for subdir in data[key]:
            if subdir not in self.ignore:
                yield os.path.join(dir_, subdir)

    def _convert_section(self, file, lesson):
        with open(file, 'r') as f:
            data = f.read()
        with open(os.path.join(self.out_dir, f'{lesson}.md'), 'a') as f:
            f.write(data)
            f.write('\n')

    def _convert_lesson(self, in_dir, sub_key):
        sections = self._sub(in_dir, sub_key)
        lesson_name = os.path.basename(in_dir)
        excs = False
        exersizes_convertor = ExersizesConvertor(in_dir, self.out_dir, lesson_name)
        for section_file in sections:
            if section_file in self.ignore:
                continue
            if os.path.basename(section_file) in ['excs']:
                excs = True
                continue
            else:
                logging.info(f'  {section_file}')
                self._convert_section(f'{section_file}.md', lesson_name)
        if excs:
            exersizes_convertor.convert()


    def convert(self, in_dir, sub_key='lessons'):
        for lesson_dir in self._sub(in_dir, sub_key):
            logging.info(f'{lesson_dir}')
            self._convert_lesson(lesson_dir, 'sections')


class ExersizesConvertor:
    def __init__(self, in_dir, out_dir, lesson):
        self.in_dir = in_dir
        self.out_dir = out_dir
        self.lesson = lesson

    def _parse_header(self, txt):
        last = False
        res = {}
        for i, l in enumerate(txt.strip().split('\n')):
            ls = l.strip()
            if ls == '---' and last:
                res['__last'] = i
                break
            elif ls == '---':
                last = True
            else:
                prop, value, *_ = re.findall(r'(.*): (.*)', ls)[0]
                res[prop] = value
        assert '__last' in res, 'header did not end with ---'
        return res


    def _convert_excs_meta(self, excs_file):
        res = defaultdict(list)
        last_title = None
        with open(excs_file, 'r') as f:
            for l in f:
                if l[:2] == '##':
                    last_title = l[2:].strip()
                    res[last_title] = []
                else:
                    ls = l.strip()
                    if ls:
                        res[last_title].append(re.findall(r'.*excs>(.*)].*', ls)[0])
            return res

    def _convert_excs(self, res):
        i = 0
        for subtitle, files in res.items():
            with open(os.path.join(self.out_dir, f'{self.lesson}.md'), 'a') as f:
                f.write(f'\n## {subtitle}\n')
                for exersize_file in files:
                    logging.info(f'    excs/{exersize_file}')
                    exersize_path = os.path.join(self.in_dir, 'excs', f'{exersize_file}.md')
                    if not os.path.exists(exersize_path):
                        logging.warning(f'{exersize_path} does not exist')
                        continue
                    with open(exersize_path) as f2:
                        data = f2.read()
                    header = self._parse_header(data)
                    rest_data = '\n'.join(data.split('\n')[header['__last']+1:])
                    f.write(f'\n### {i}. {header["title"]}\n')
                    f.write(f'Obtížnost: {header["demand"]}\n\n')
                    f.write(rest_data)
                    i += 1


    def convert(self):
        res = self._convert_excs_meta(os.path.join(self.in_dir, 'excs.md'))
        self._convert_excs(res)


if __name__=='__main__':
    logging.basicConfig(level=logging.INFO)
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('in_dir', type=str)
    parser.add_argument('out_dir', type=str)
    parser.add_argument('-f', '--force', action='store_true')
    parser.add_argument('--ignore', nargs='+', default=['excs.md'])
    args = parser.parse_args()


    convertor = Convertor(args.out_dir, args.ignore, args.force)
    convertor.convert(args.in_dir)

