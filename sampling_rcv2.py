# Copyright (c) 2017-present, Facebook, Inc.
# All rights reserved.
#
# This source code is licensed under the license found in the
# LICENSE file in the root directory of this source tree.
#
#!/usr/bin/env python3
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals
import codecs
import os
import random
import numpy as np
import argparse


def check_data_sufficiency(
    example_counts,
    num_samples,
    label_priors,
    threshold,
):
    for label, prob in label_priors.items():
        min_required_samples = num_samples * prob * threshold
        if min_required_samples <= 0 or min_required_samples > example_counts[label]:
            return False

    return True


def generate_samples(
    input_file,
    output_dir,
    dialect,
    label_priors,
    threshold,
    num_test=4000,
    num_dev=1000,
    min_num_train=1000,
):
    np.random.seed(1234)
    examples = {'C': [], 'E': [], 'G': [], 'M': []}
    with codecs.open(input_file, "r", "utf-8") as input_stream:
        invalid_examples = 0
        for line in input_stream:
            try:
                label, doc = line.strip().split('\t')
                examples[label].append(doc)
            except Exception as e:
                invalid_examples += 1
        print('Filtered {} invalid examples.'.format(invalid_examples))

    for label in examples.keys():
        examples[label] = list(set(examples[label]))
        random.shuffle(examples[label])

    example_counts = {k: len(v) for k, v in examples.items()}
    total_exp = sum([len(v) for v in examples.values()])
    emp_prior = {k: round(len(v) / total_exp, 3) for k, v in examples.items()}
    print('Empirical class prior for {}'.format(dialect))
    print(emp_prior)
    num_samples = min_num_train + num_dev + num_test
    if check_data_sufficiency(
        example_counts,
        num_samples,
        label_priors,
        threshold,
    ):
        label_required_min = {}
        for label, prob in label_priors.items():
            if example_counts[label] >= num_samples * prob:
                label_required_min[label] = num_samples * prob
            else:
                label_required_min[label] = (
                    example_counts[label] * num_samples /
                    (num_samples + min_num_train * 2)
                )
        total_required_min = sum(label_required_min.values())
        all_labels = [label for label, _ in label_required_min.items()]
        updated_label_priors = [
            min_count / total_required_min for _, min_count
            in label_required_min.items()
        ]
        print("Start sampling {} with balanced class prior:".format(dialect))
        print(updated_label_priors)

        train_size_factors = [1, 2, 5, 10, 20]
        train_sizes = [min_num_train * k for k in train_size_factors]

        train_sets = []
        train_files = []
        dev_file = codecs.open(
            os.path.join(output_dir, '{}.dev'.format(dialect)),
            'w',
            encoding="utf-8",
        )
        test_file = codecs.open(
            os.path.join(output_dir, '{}.test'.format(dialect)),
            'w',
            encoding="utf-8",
        )

        i = 0
        num_classes = len(examples.keys())
        while i < min(total_exp, train_sizes[-1] + num_dev + num_test):
            labels = [k for k in examples.keys() if len(examples[k]) > 0]
            if len(labels) == num_classes:
                label = all_labels[np.random.choice(
                    num_classes, 1, p=updated_label_priors)[0]]
            else:
                label = labels[np.random.randint(len(labels))]
            ex = '{}\t{}\n'.format(label, examples[label][-1])
            examples[label].pop()
            if i < num_test:
                test_file.write(ex)
            elif i < (num_test + num_dev):
                dev_file.write(ex)
            elif i < (num_test + num_dev + train_sizes[0]):
                if len(train_sets) == 0:
                    train_sets.append([])
                    train_files.append(
                        codecs.open(
                            os.path.join(
                                output_dir,
                                '{}.train.{}'.format(
                                    dialect,
                                    train_sizes[0],
                                ),
                            ),
                            'w',
                            encoding='utf-8',
                        )
                    )
                train_sets[0].append(ex)
            elif i < (num_test + num_dev + train_sizes[1]):
                if len(train_sets) == 1:
                    train_sets.append([])
                    train_files.append(
                        codecs.open(
                            os.path.join(
                                output_dir,
                                '{}.train.{}'.format(
                                    dialect,
                                    train_sizes[1],
                                ),
                            ),
                            'w',
                            encoding='utf-8',
                        )
                    )
                train_sets[1].append(ex)
            elif i < (num_test + num_dev + train_sizes[2]):
                if len(train_sets) == 2:
                    train_sets.append([])
                    train_files.append(
                        codecs.open(
                            os.path.join(
                                output_dir,
                                '{}.train.{}'.format(
                                    dialect,
                                    train_sizes[2],
                                ),
                            ),
                            'w',
                            encoding='utf-8',
                        )
                    )
                train_sets[2].append(ex)
            elif i < (num_test + num_dev + train_sizes[3]):
                if len(train_sets) == 3:
                    train_sets.append([])
                    train_files.append(
                        codecs.open(
                            os.path.join(
                                output_dir,
                                '{}.train.{}'.format(
                                    dialect,
                                    train_sizes[3],
                                ),
                            ),
                            'w',
                            encoding='utf-8',
                        )
                    )
                train_sets[3].append(ex)
            elif i < (num_test + num_dev + train_sizes[4]):
                if len(train_sets) == 4:
                    train_sets.append([])
                    train_files.append(
                        codecs.open(
                            os.path.join(
                                output_dir,
                                '{}.train.{}'.format(
                                    dialect,
                                    train_sizes[4],
                                ),
                            ),
                            'w',
                            encoding='utf-8',
                        )
                    )
                train_sets[4].append(ex)
            else:
                print("Finished sampling")
                break
            i += 1

        dev_file.close()
        test_file.close()

        for i in range(len(train_sets)):
            random.shuffle(train_sets[i])
            for ex in train_sets[i]:
                train_files[i].write(ex)
            train_files[i].close()
            if i < (len(train_sets) - 1):
                train_sets[i + 1].extend(train_sets[i])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        dest='threshold',
        help='ratio of expected number of examples if uniform prior',
    )
    parser.add_argument(
        dest='input_dir',
        help='directory of rcv2 stories to sample from',
    )
    parser.add_argument(
        dest='output_dir',
        help='directory to store samples',
    )
    parser.add_argument(
        dest='num_test',
        help='number of test examples',
    )
    parser.add_argument(
        dest='num_dev',
        help='number of dev examples',
    )
    parser.add_argument(
        dest='min_num_train',
        help='minimal number of train examples',
    )
    args = parser.parse_args()

    class_prior = [0.25, 0.25, 0.25, 0.25]

    labels = ['C', 'E', 'G', 'M']
    class_prior_dict = dict(zip(labels, class_prior))

    for current_path, _, dialects in os.walk(args.input_dir):
        for dialect in dialects:
            generate_samples(
                os.sep.join([current_path, dialect]),
                args.output_dir,
                dialect,
                class_prior_dict,
                float(args.threshold),
                int(args.num_test),
                int(args.num_dev),
                int(args.min_num_train),
            )
            print("Finished sampling {}".format(dialect))


if __name__ == '__main__':
    main()