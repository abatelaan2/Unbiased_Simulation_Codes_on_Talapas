import os
import argparse

parser = argparse.ArgumentParser()

parser.add_argument('-run_name', '--run_name', help="name of run")
parser.add_argument('-prot_name', '--prot_name', help="name of protein")

args = parser.parse_args()

#Write run_pro_GPU_gmx_mpi.sh
run_pro_GPU_gmx_mpi_text = f"""#!/bin/bash
#SBATCH --partition=gpu       ### queue to submit to
#SBATCH --job-name=run_pro_GPU_gmx_mpi_{args.run_name}        ### job name
#SBATCH --output=run_pro_GPU_gmx_mpi_{args.run_name}_jobout         ### file in which to store job stdout
#SBATCH --error=run_pro_GPU_gmx_mpi_{args.run_name}_joberr          ### file in which to store job stderr
#SBATCH --time=00-00:30:00        ### Wall clock time limit in HH:MM:SS
#SBATCH --nodes=1               ### number of nodes to use
#SBATCH --mem=32G
#SBATCH --ntasks-per-node=1    ### nuimber of tasks to launch per node
#SBATCH --account=ch447_547      ### Account used for job submission
#SBATCH --gpus-per-task=1
#SBATCH --constraint=gpu-40gb

module purge
#module load gromacs/2024.1
module load gromacs/2024.3-plumed-2.11.0-cuda-12.4.1

run_name=$1
prot_name=$2
ion_dir=$3
em_dir=$4
npt_dir=$5
pro_dir="pro"
res_dir="res"
iteration=1

start_time=$(date +%s)  # Get start time in seconds
echo "Job started at: $(date)" >> ./${{pro_dir}}/execution_time_pro.txt

#run_name="test_11-28-23"
#prot_name="gp32openwithzn"
#ion_dir="ions"
#em_dir="em"
#npt_dir="npt"
#pro_dir="pro"

#mkdir ./${{run_name}}/${{pro_dir}}/prod${{iteration}}

gmx_mpi grompp -f ./${{pro_dir}}/pro.mdp \
    -c ./${{npt_dir}}/npt_${{prot_name}}.gro \
    -r ./${{npt_dir}}/npt_${{prot_name}}.gro \
    -o ./${{pro_dir}}/pro_${{prot_name}}.tpr \
    -p ./sys.top -maxwarn 5

#mpirun gmx_mpi mdrun -v -s ./${{run_name}}/${{pro_dir}}/pro_${{prot_name}}.tpr \
#    -o ./${{run_name}}/${{pro_dir}}/pro_${{prot_name}}.trr \
#    -c ./${{run_name}}/${{em_dir}}/em_${{prot_name}}.gro \
#    -g ./${{run_name}}/${{pro_dir}}/pro_${{prot_name}}.log \
#    -ntomp 1

export OMP_NUMP_THREADS=4
#export OMP_NUMP_THREADS=2
    
mpiexec -n 1 gmx_mpi mdrun -v -s ./${{pro_dir}}/pro_${{prot_name}}.tpr \
    -g ./${{pro_dir}}/pro_${{prot_name}}.log \
    -c ./${{pro_dir}}/pro_${{prot_name}}.gro \
    -x ./${{pro_dir}}/pro_${{prot_name}}_traj_comp.xtc \
    -e ./${{pro_dir}}/pro_edr.edr \
    -cpo ./${{pro_dir}}/state.cpt \
    -nsteps 500000 \
    -append
    -pin on -pinoffset 0 -gpu_id 0
    
#    -nsteps 50000000 \  this is 100 ns
#    -nsteps 500000 \ this is 1 ns
#    -nsteps 5000 \ this is 10 ps
    
#the production run needs a npt/gro equilibrated topology file for -c option (fix this)

gmx dump -cp ./${{pro_dir}}/state.cpt > ./${{pro_dir}}/checkpoint_info.txt

end_time=$(date +%s)  # Get end time in seconds
elapsed_time=$((end_time - start_time))  # Compute elapsed time

echo "Job ended at: $(date)" >> ./${{pro_dir}}/execution_time_pro.txt
echo "Elapsed time: $elapsed_time seconds" >> ./${{pro_dir}}/execution_time_pro.txt

next_iteration=$((iteration + 1))
sbatch run_fromrestart_{args.run_name}.sh ${{run_name}} ${{prot_name}} ${{ion_dir}} ${{em_dir}} ${{npt_dir}} ${{pro_dir}} ${{next_iteration}}

#Example
#sbatch run_pro_GPU_gmx_mpi.sh test_12-06-24 dialanine ions em npt
#sbatch run_pro_GPU_gmx_mpi.sh Na_100_Mg_6_GP32open_1microsecond GP32open ions em npt
"""

with open(f'run_pro_GPU_gmx_mpi_{args.run_name}.sh', 'w') as w:
    w.write(run_pro_GPU_gmx_mpi_text)
    
#Write run_fromrestart.sh
    
run_fromrestart_text = f"""#!/bin/bash
#SBATCH --partition=gpu       ### queue to submit to
#SBATCH --job-name=run_from_restart_GPU_gmx_mpi_{args.run_name}        ### job name
#SBATCH --output=run_from_restart_GPU_gmx_mpi_{args.run_name}_jobout         ### file in which to store job stdout
#SBATCH --error=run_from_restart_GPU_gmx_mpi_{args.run_name}_joberr          ### file in which to store job stderr
#SBATCH --time=00-00:30:00        ### Wall clock time limit in HH:MM:SS
#SBATCH --nodes=1               ### number of nodes to use
#SBATCH --mem=32G
#SBATCH --ntasks-per-node=1    ### nuimber of tasks to launch per node
#SBATCH --account=ch447_547      ### Account used for job submission
#SBATCH --gpus-per-task=1
#SBATCH --constraint=gpu-40gb

module purge
#module load gromacs/2024.1
module load gromacs/2024.3-plumed-2.11.0-cuda-12.4.1
###########################################

# other variables
#run_name="test_09-24-24"
#prot_name="gp32openwithzn"
#ion_dir="ions"
#em_dir="em"
#npt_dir="npt"
#pro_dir="pro"

# other variables
run_name=$1
prot_name=$2
ion_dir=$3
em_dir=$4
npt_dir=$5
pro_dir=$6
iteration=$7

start_time=$(date +%s)  # Get start time in seconds
echo "Job started at: $(date)" >> ./${{pro_dir}}/execution_time_pro_restart_${{iteration}}.txt

#mkdir ./${{run_name}}/${{pro_dir}}/prod${{iteration}}

gmx_mpi convert-tpr -s ./${{pro_dir}}/pro_${{prot_name}}.tpr \
    -extend 1000 \
    -o ./${{pro_dir}}/pro_${{prot_name}}.tpr
    
#extend for 100000; means extend 100000 ps = 100 ns
#extend for 1000; means means extend 1 ns
#extend for 10; means means extend 10 ps

#export OMP_NUMP_THREADS=2
export OMP_NUMP_THREADS=4
    
mpiexec -n 1 gmx_mpi mdrun -v -s ./${{pro_dir}}/pro_${{prot_name}}.tpr \
    -cpi ./${{pro_dir}}/state.cpt \
    -g ./${{pro_dir}}/pro_${{prot_name}}.log \
    -x ./${{pro_dir}}/pro_${{prot_name}}_traj_comp.xtc \
    -e ./${{pro_dir}}/pro_edr.edr \
    -cpo ./${{pro_dir}}/state.cpt \
    -append
    -pin on -pinoffset 0 -gpu_id 0
    
gmx dump -cp ./${{pro_dir}}/state.cpt > ./${{pro_dir}}/checkpoint_info.txt

end_time=$(date +%s)  # Get end time in seconds
elapsed_time=$((end_time - start_time))  # Compute elapsed time

echo "Job ended at: $(date)" >> ./${{pro_dir}}/execution_time_pro_restart_${{iteration}}.txt
echo "Elapsed time: $elapsed_time seconds" >> ./${{pro_dir}}/execution_time_pro_restart_${{iteration}}.txt
    
if [ $iteration -lt 3 ]
then
    next_iteration=$((iteration + 1))
    sbatch run_fromrestart_{args.run_name}.sh ${{run_name}} ${{prot_name}} ${{ion_dir}} ${{em_dir}} ${{npt_dir}} ${{pro_dir}} ${{next_iteration}}
    exit
else
    echo 'jobs done'
    exit
fi

#Example
#sbatch run_fromrestart.sh test_12-06-24 dialanine ions em npt
#sbatch run_fromrestart.sh Na_100_Mg_6_GP32open_1microsecond GP32open ions em npt pro 2
#sbatch run_fromrestart.sh Na_100_Mg_6_GP32closed_1microsecond GP32closed ions em npt pro 3"""

with open(f'run_fromrestart_{args.run_name}.sh', 'w') as w:
    w.write(run_fromrestart_text)
    

os.system(f"mv run_pro_GPU_gmx_mpi_{args.run_name}.sh {args.run_name}/run_pro_GPU_gmx_mpi_{args.run_name}.sh")
os.system(f"mv run_fromrestart_{args.run_name}.sh {args.run_name}/run_fromrestart_{args.run_name}.sh")
os.system(f"cd {args.run_name}; sbatch run_pro_GPU_gmx_mpi_{args.run_name}.sh {args.run_name} {args.prot_name} ions em npt")

#Example
#python3 write_GROMACS_production_codes.py -run_name Na_100_Mg_6_GP32open_1microsecond -prot_name GP32open
#python3 write_GROMACS_production_codes.py -run_name Na_100_Mg_6_GP32closed_1microsecond -prot_name GP32closed
