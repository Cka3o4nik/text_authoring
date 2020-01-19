Основной скрипт - srilm_utils.py. его параметры:

Создание модели по папке с исходными файлами:
create_full_lm order src_path file_mask dst_path tmp_path [vocab_file] [smooth_args]

Создание статистики:
create_ngram_stats order src_path file_mask dst_path tmp_path [prev_stats]

Создание модели по готовой статистике:
create_lm order src_path dst_path [vocab_file] [smooth_args]
