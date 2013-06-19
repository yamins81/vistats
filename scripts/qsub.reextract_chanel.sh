#!/bin/bash
#$ -S /bin/bash
#$ -V 
#$ -cwd


DB1=None
DB2=devthor_reextract_vistats_chanel
HOST1=localhost
PORT1=22334
HOST2=localhost
PORT2=22334
IND=$(expr $SGE_TASK_ID - 1)
IDFILE=/home/render/devthor/devthor/tpe_balance_combinations/new_all_id_list_small.pkl
export BASEDIR=/home/devthor_vistats_chanel
K=1

#export THEANO_FLAGS=compile_dir=.compile_dir_$IND

python -c "import vistats.datasets as vd;  vd.extract_on_vistats_chanel_dataset($IND, '$HOST1', '$HOST2', $PORT1, $PORT2, '$DB1', '$DB2', '$IDFILE', $K)"
