#!/bin/bash
#SBATCH --partition=computelong       ### queue to submit to
#SBATCH --job-name=npteq        ### job name
#SBATCH --output=npteq_jobout         ### file in which to store job stdout
#SBATCH --error=npteq_joberr          ### file in which to store job stderr
#SBATCH --time=1-23:59:00        ### Wall clock time limit in HH:MM:SS
#SBATCH --nodes=1               ### number of nodes to use
#SBATCH --ntasks-per-node=24    ### nuimber of tasks to launch per node
#SBATCH --cpus-per-task=1       ### number of cores for each task
#SBATCH --account=ch447_547      ### Account used for job submission

module purge
module load gromacs/2024.1

run_name=$1
protname=$2
ion_dir=$3
em_dir=$4
nvt_dir="nvt"
npt_dir="npt"

#run_name="test_9-25-23"
#prot_name="GP32openwithZn"
#ion_dir="ions"
#em_dir="em"
#npt_dir="npt"

gmx_mpi grompp -f ./${run_name}/${npt_dir}/npt.mdp \
    -c ./${run_name}/${nvt_dir}/nvt_${protname}.gro \
    -r ./${run_name}/${nvt_dir}/nvt_${protname}.gro \
    -o ./${run_name}/${npt_dir}/npt_${protname}.tpr \
    -p ./${run_name}/sys.top -maxwarn 5

export OMP_NUMP_THREADS=2

mpiexec -n 1 gmx_mpi mdrun -s ./${run_name}/${npt_dir}/npt_${protname}.tpr \
    -o ./${run_name}/${npt_dir}/npt_${protname}.trr \
    -c ./${run_name}/${npt_dir}/npt_${protname}.gro \
    -g ./${run_name}/${npt_dir}/npt_${protname}.log \
    -e ./${run_name}/${npt_dir}/npt_${protname}.edr \
    -pin on -pinoffset 0

#gmx_mpi trjconv -s ${run_name}/${npt_dir}/npt_${protname}.tpr \
#                -f ${run_name}/${npt_dir}/npt_${protname}.trr \
#                -o ${run_name}/${npt_dir}/npt_${protname}.gro \
#                -dump -1

    
#sbatch run_pro_GPU_gmx_mpi.sh ${run_name} ${protname} ${ion_dir} ${em_dir} ${npt_dir}
