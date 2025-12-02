#!/bin/bash
#SBATCH --partition=compute       ### queue to submit to
#SBATCH --job-name=em        ### job name
#SBATCH --output=em_jobout         ### file in which to store job stdout
#SBATCH --error=em_joberr          ### file in which to store job stderr
#SBATCH --time=0-04:00:00        ### Wall clock time limit in HH:MM:SS
#SBATCH --nodes=2               ### number of nodes to use
#SBATCH --ntasks-per-node=24    ### nuimber of tasks to launch per node
#SBATCH --cpus-per-task=1       ### number of cores for each task
#SBATCH --account=ch447_547      ### Account used for job submission

### runs md from scratch, copying from the base directory
module purge
module load gromacs/2024.1

run_name=$1

source "${run_name}/${run_name}_config.sh"


# energy minimzation

gmx_mpi grompp -v -f ./${run_name}/${em_dir}/em.mdp \
    -c ./${run_name}/${ion_dir}/ion_${protname}.gro \
    -o ./${run_name}/${em_dir}/em_${protname}.tpr \
    -p ./${run_name}/sys.top

export OMP_NUMP_THREADS=2

mpiexec -n 1 gmx_mpi mdrun -v -s ./${run_name}/${em_dir}/em_${protname}.tpr \
    -o ./${run_name}/${em_dir}/em_${protname}.trr \
    -c ./${run_name}/${em_dir}/em_${protname}.gro \
    -g ./${run_name}/${em_dir}/em_${protname}.log \
    -pin on -pinoffset 0
    
sbatch 2_run_nvteq_generalized.sh ${run_name} ${protname} ${ion_dir} ${em_dir}
