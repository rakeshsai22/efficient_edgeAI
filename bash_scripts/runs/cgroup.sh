# The `cgcreate` command is used to create **control groups (cgroups)** in Linux. Cgroups are a kernel feature that allows you to allocate, limit, and monitor system resources (such as CPU, memory, disk I/O, etc.) for a group of processes. This is particularly useful for managing resource usage in multi-process environments, such as containers, virtual machines, or even regular applications.

# Why Use `cgcreate`?
# The `cgcreate` command is used to create a new cgroup hierarchy or add a new cgroup to an existing hierarchy. Once a cgroup is created, you can:
# 1. Limit Resource Usage**: Restrict how much CPU, memory, or other resources processes in the cgroup can use.
# 2. Prioritize Resources**: Assign higher or lower priority to certain processes.
# 3. Monitor Resource Usage**: Track how much CPU, memory, or other resources are being used by processes in the cgroup.
# 4. Isolate Processes**: Ensure that processes in one cgroup do not interfere with processes in another cgroup.


#Command Breakdown
# The `cgcreate` command has the following syntax:
# ```bash
# cgcreate -g <controllers>:<path>
# ```

# #### Key Options:
# 1. **`-g <controllers>:<path>`**:
#    - `<controllers>`: Specifies the resource controllers (e.g., `cpu`, `memory`, `blkio`) to be used for the cgroup.
#    - `<path>`: Specifies the path to the new cgroup. This path is relative to the cgroup mount point (usually `/sys/fs/cgroup`).

#    Example:
#    ```bash
#    cgcreate -g cpu:/mygroup
#    ```
#    This creates a new cgroup named `mygroup` under the `cpu` controller.

# 2. **`-a <tuid>:<tgid>`**:
#    - Sets the owner of the cgroup and all its files. `<tuid>` is the user ID, and `<tgid>` is the group ID.

# 3. **`-d <mode>`**:
#    - Sets the permissions for the cgroup directory (e.g., `755`).

# 4. **`-f <mode>`**:
#    - Sets the permissions for the files within the cgroup (e.g., `644`).

# 5. **`-t <tuid>:<tgid>`**:
#    - Sets the owner of the `tasks` file in the cgroup. This file contains the list of processes in the cgroup.

# 6. **`-h` or `--help`**:
#    - Displays help information for the command.

# ---

# ### Example Usage
# #### 1. Create a Cgroup for CPU Control
# To create a cgroup named `limited_cpu` under the `cpu` controller:
# ```bash
# sudo cgcreate -g cpu:/limited_cpu
# ```
# This creates a directory at `/sys/fs/cgroup/cpu/limited_cpu` with files for managing CPU resources.

# #### 2. Set CPU Quota
# After creating the cgroup, you can limit the CPU usage for processes in the cgroup. For example, to limit the CPU usage to 50% of a single core:
# ```bash
# echo 100000 > /sys/fs/cgroup/cpu/limited_cpu/cpu.cfs_quota_us
# echo 100000 > /sys/fs/cgroup/cpu/limited_cpu/cpu.cfs_period_us
# ```
# - `cpu.cfs_quota_us`: The maximum CPU time (in microseconds) that processes in the cgroup can use in one period.
# - `cpu.cfs_period_us`: The length of the period (in microseconds).

# #### 3. Add a Process to the Cgroup
# To add a process to the cgroup, write its PID to the `tasks` file:
# ```bash
# echo <PID> > /sys/fs/cgroup/cpu/limited_cpu/tasks
# ```

# #### 4. Run a Process in the Cgroup
# You can also start a process directly in the cgroup using `cgexec`:
# ```bash
# sudo cgexec -g cpu:/limited_cpu my_command
# ```


# to dynamically limit the number of CPU cores used by the Python process based on certain conditions (e.g., `prefix_hit`). Using `cgcreate` and `cgset`, you can:
# 1. Create a cgroup for the Python process.
# 2. Dynamically adjust the CPU quota for the cgroup based on the value of `prefix_hit`.
# 3. Ensure that the Python process does not exceed the allocated CPU resources.


# Here’s how you can use `cgcreate` and `cgset` in your script:

# ```bash
# # Create a cgroup for CPU control
# sudo cgcreate -g cpu:/limited_cpu

# # Start the Python process in the cgroup
# sudo cgexec -g cpu:/limited_cpu python3 "$PYTHON_SCRIPT" > "$OUTPUT_FILE" 2>&1 &
# PYTHON_PID=$!

# # Function to limit CPU cores
# limit_cores() {
#     local cores=$1
#     local quota=$((cores * 100000)) # 100000 µs per core
#     echo "Limiting to $cores core(s)..."
#     sudo cgset -r cpu.cfs_quota_us=$quota limited_cpu
# }

# # Adjust CPU quota based on prefix_hit
# if [[ $prefix_hit -ge 50 ]]; then
#     limit_cores 2
# elif [[ $prefix_hit -lt 50 ]]; then
#     limit_cores 4
# fi

# # Clean up the cgroup after the script finishes
# sudo cgdelete cpu:/limited_cpu
# ```

# ---

# ### Summary
# - **`cgcreate`** is used to create a cgroup for managing resources like CPU, memory, etc.
# - **`cgset`** is used to configure resource limits for the cgroup.
# - **`cgexec`** is used to run a process within the cgroup.
# - This approach is powerful for dynamically controlling resource usage in your script. However, it requires `cgroup-tools` to be installed and root privileges.