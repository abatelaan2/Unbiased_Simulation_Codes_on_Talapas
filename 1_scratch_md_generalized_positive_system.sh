#!/bin/bash
#SBATCH --partition=compute       ### queue to submit to
#SBATCH --job-name=GROMACS_Talapas2        ### job name
#SBATCH --output=jobout         ### file in which to store job stdout
#SBATCH --error=joberr          ### file in which to store job stderr
#SBATCH --time=0-04:00:00        ### Wall clock time limit in HH:MM:SS
#SBATCH --nodes=1               ### number of nodes to use
#SBATCH --ntasks-per-node=28     ### number of tasks to launch per node
#SBATCH --cpus-per-task=1       ### number of cores for each task
#SBATCH --account=ch447_547      ### Account used for job submission

### runs md from scratch, copying from the base directory
module purge
module load slurm
module load gromacs/2024.1
module load openmpi

module load spack-rhel8
spack load /as4clij
module load amber/22
module load python3/3.10.13

######################################################
##Specify Inputs
############################################################

# variables
## protein related

# Usage: ./run.sh base_folder_name

base_dir=$1
run_name=$2

#############################################################
## copy base directory and move into folder
#############################################################
cp -n -r "$base_dir" "${run_name}"
wait

cp "${run_name}_config.sh" "${run_name}"/

#############################################################

source "${run_name}/${run_name}_config.sh"

#############################################################

cd ${run_name}

mkdir config

cp ./${pdb} config/

cd config
#############################################################

#############################################################
##clean pdb and create simulation box
###############################################################
pdb4amber -i ./${pdb} -o cleaned.pdb --nohyd #remove hydrogens
pdb4amber -i cleaned.pdb -o add_hydrogens.pdb -y #add hydrogens back in


## write tleap_solvate.in
cat > tleap_solvate.in << EOF
source leaprc.protein.ff19SB
source leaprc.water.tip3p
#source leaprc.DNA.OL21

system = loadpdb add_hydrogens.pdb 
solvateBox system TIP3PBOX 14 iso
quit
EOF

tleap -f tleap_solvate.in > tleap_solvate.log
#############################################################

################################################################
## calculate number of ions needed for specific concentration
################################################################

# Read tleap.log and extract the volume number and clean it up
volume=$(grep "Volume:" tleap_solvate.log | awk '{print $2}')
#volume=$(grep "Volume:" tleap.log | sed -E 's/[^0-9\.]//g')

## Calculate number of ions needed
cat > multiply.py << EOF
import numpy as np

volume_l=$volume*(1*10**-27)

no_atoms_Na=$na_conc * (6.022*(10**23))
no_ions_Na=round(no_atoms_Na * volume_l)

no_atoms_Mg=$mg_conc * (6.022*(10**23))
no_ions_Mg=round(no_atoms_Mg * volume_l)

print(no_ions_Na)
print(no_ions_Mg)

EOF

mapfile -t lines < <(python3 multiply.py)

no_ions_Na=${lines[0]}
no_ions_Mg=${lines[1]}

echo "no_ions_Na: ${no_ions_Na}"
echo "no_ions_Mg: ${no_ions_Mg}"

no_ions_Cl_with_Mg=$((2 * no_ions_Mg))

echo "no_ions_Cl_with_Mg: ${no_ions_Cl_with_Mg}"

#########################################################

###############################################################
##Neutralize and add ions to the system
###############################################################

## write tleap.in
cat > tleap.in << EOF
source leaprc.protein.ff19SB
source leaprc.water.tip3p
#source leaprc.DNA.OL21

system = loadpdb add_hydrogens.pdb
solvateBox system TIP3PBOX 14 iso
addIonsRand system Cl- 0
addIonsRand system Na+  ${no_ions_Na}  Cl- ${no_ions_Na}
addIonsRand system MG ${no_ions_Mg}  Cl- ${no_ions_Cl_with_Mg}
savePDB system ../${em_dir}/${protname}.pdb
saveAmberParm system ../${em_dir}/${protname}.parm7 ../${em_dir}/${protname}.rst7
quit
EOF

tleap -f tleap.in > tleap.log
##############################################################

###########################################################
##Move into em folder and convert from amber to gromacs
#############################################################

cd ../
cd em/

##convert to gromacs input
pip install parmed

cat > convert_parmed.py << EOF
import parmed as pmd
parm = pmd.load_file('${protname}.parm7', '${protname}.rst7')
parm.save('../sys.top', format='gromacs')
parm.save('../${ion_dir}/ion_${protname}.gro')

EOF

python3 convert_parmed.py

############################################################

