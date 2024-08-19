import os
import shutil
import json

def retrieve_workers(workers, default):
    if workers:
        return f"-w {workers}"
    else:
        return f"-w {default}"

def retrieve_R_version(version):
    if version == "4.2.2":
        return f"module load GCC/12.2.0  OpenMPI/4.1.4 R_tamu/4.2.2"
    else:
        return f""

def retrieve_R_driver(mpistring):
    if mpistring == "mpi":
        return f"mpirun -np 1 "
    else:
        return f""

def retrieve_alphapickle(pickle, proteinfasta, outputdir):
    if pickle == "true":
       name = os.path.splitext(os.path.basename(proteinfasta))[0]
       return f"run_AlphaPickle.py   -od " +  outputdir + "/" + name
    else:
       return f""

def retrieve_loaded_modules(modules):
    if modules == "":
        return f""
    else:
        return "module load foss/2023a " + modules



def retrieve_R_version_grace(version):
    if version == "4.1.2":
        return f"module load foss/2021b R_tamu/4.1.2"
    elif version == "4.2.0":
        return f"module load foss/2021b R_tamu/4.2.0"
    else:
        return f"module load foss/2022b R_tamu/4.3.1"


def retrieve_loaded_modules_grace(modules):
    if modules == "":
        return f""
    else:
        return "module load foss/2023a " + modules

def retrieve_mpi_mode_abaqus(cores, limit ):
    if cores > limit:
        return f"mp_mode=mpi"
    else:
        return f""

def retrieve_umat_abaqus(umat ):
    if umat != "":
        return f"user="+umat+" "
    else:
        return f""


def retrieve_ncpus(cores,parallel):
    if parallel == "yes":
        return f"ncpus=" +cores
    else:
        return f""

def retrieve_tamubatch_opts(cores,memory,walltime,extra_slurm="",gpu=""):
    options_string=""
    additional=extra_slurm + " " + gpu
    if  cores != "":
        options_string=options_string+"-n " + cores + " "
    if walltime != "":
        times=walltime.split(':')
        if int(times[0]) > 168:
            additional=additional+ " --partition xlong " 
        options_string=options_string+"-W " + walltime + " "
    if memory.find("MB") > 0 or memory.find("G") > 0:
        options_string=options_string+"-M " + memory + " "
    if additional != "":
        options_string="-x '" + additional + "' " + options_string
    return f"" + options_string



def retrieve_mopts(workers,threads,walltime,memory,extra_params):
    options_string=""
    additional=extra_params = exta_params + " " + gpu + " "
    if workers != "" and workers != "0":
        options_string="-w " + workers + " " + options_string
    if threads != "" :
        options_string="-s " + threads + " " + options_string
    if walltime != "":
        times=walltime.split(':')
        if int(times[0]) > 168:
            aditional=additional+ "--partition xlong "
        options_string="-t " + walltime + " " + options_string
    if memory != "MB":
        memory=memory[:-2]
        options_string="-m " + memory + " " + options_string
    if extra_params != "":
        options_string="-x '" + additional + "' " + options_string
    return f"" + options_string


def drona_add_additional_file(job_name, additional_file):
    additional_files_path = os.path.join("/tmp", f"{job_name}.additional_files")
    if os.path.exists(additional_files_path):
        with open(additional_files_path, 'r') as file:
            additional_files = json.load(file)
    else:
        additional_files = {'files': []}    
    
    additional_files['files'].append(additional_file)
    with open(additional_files_path, "w") as file:
        json.dump(additional_files, file)


def drona_add_warning(job_name, warning):
    warnings_path = os.path.join("/tmp", f"{job_name}.warnings")
    if os.path.exists(warnings_path):
        with open(warnings_path, 'r') as file:
            warnings = json.load(file)
    else:
        warnings = {'warnings': []}    
    
    warnings['warnings'].append(warning)
    with open(warnings_path, "w") as file:
        json.dump(warnings, file)

