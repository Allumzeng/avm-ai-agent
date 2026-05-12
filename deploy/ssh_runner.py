"""SSH helper to run commands on the VPS."""
import paramiko
import sys

HOST = "187.124.43.165"
USER = "root"
PASSWORD = "Zengenjie0702#"


def run(cmd, timeout=300):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=15)
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout, get_pty=True)
    out = stdout.read().decode(errors="replace")
    err = stderr.read().decode(errors="replace")
    exit_code = stdout.channel.recv_exit_status()
    client.close()
    print(f"--- exit={exit_code} ---")
    if out.strip():
        print("STDOUT:")
        print(out)
    if err.strip():
        print("STDERR:")
        print(err)
    return exit_code, out, err


if __name__ == "__main__":
    run(sys.argv[1])
