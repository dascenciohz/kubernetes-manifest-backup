#!/usr/bin/env python3

import os
from kubernetes import client, config
import subprocess

# Configurar acceso al clúster de Kubernetes
config.load_kube_config()

# Crear una instancia de la API de Kubernetes
client_v1 = client.CoreV1Api()
apps_v1 = client.AppsV1Api()
autoscaling_v1 = client.AutoscalingV1Api()
custom_objects_api = client.CustomObjectsApi()

# Obtener todos los namespaces
namespaces = client_v1.list_namespace().items

# Lista de namespaces a excluir
namespaces_exclude = ["kube-system", "kube-node-lease", "kube-public", "default", "dynatrace", "monitoring", "castai-agent", "gke-managed-system", "emissary-system", "ambassador"]

# Crear directorio de respaldo si no existe
backup_dir = "full-backup-k8s"
os.makedirs(backup_dir, exist_ok=True)

def run_command(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[!] Error ejecutando el comando: {command}\n{result.stderr}")
    return result.stdout

# Recorrer todos los namespaces y respaldar recursos
for namespace in namespaces:
    namespace_name = namespace.metadata.name
    namespace_dir = os.path.join(backup_dir, namespace_name)
    os.makedirs(namespace_dir, exist_ok=True)
    if namespace_name not in namespaces_exclude:
        print(f"\n[+] Respaldando recursos del namespace: {namespace_name}")
        # Respaldar Deployments
        deployments = apps_v1.list_namespaced_deployment(namespace_name).items
        for deployment in deployments:
            deployment_name = deployment.metadata.name
            if "default" and "kube-root-ca" not in deployment_name:
                print(f"\t[+] Respaldando el recurso deployment llamado {deployment_name}")
                yaml_output = run_command(f"kubectl get -o yaml -n {namespace_name} deploy {deployment_name}")
                with open(f"{namespace_dir}/deployment-{deployment_name}.yaml", "w") as file:
                    file.write(yaml_output)
        
        # Respaldar Services
        services = client_v1.list_namespaced_service(namespace_name).items
        for service in services:
            service_name = service.metadata.name
            if "default" and "kube-root-ca" not in service_name:
                print(f"\t[+] Respaldando el recurso service llamado {service_name}")
                yaml_output = run_command(f"kubectl get -o yaml -n {namespace_name} service {service_name}")
                with open(f"{namespace_dir}/service-{service_name}.yaml", "w") as file:
                    file.write(yaml_output)

        # Respaldar HPAs
        hpas = autoscaling_v1.list_namespaced_horizontal_pod_autoscaler(namespace_name).items
        for hpa in hpas:
            hpa_name = hpa.metadata.name
            if "default" and "kube-root-ca" not in hpa_name:
                print(f"\t[+] Respaldando el recurso hpa llamado {hpa_name}")
                yaml_output = run_command(f"kubectl get -o yaml -n {namespace_name} hpa {hpa_name}")
                with open(f"{namespace_dir}/hpa-{hpa_name}.yaml", "w") as file:
                    file.write(yaml_output)
        
        # Respaldar ServiceAccounts
        serviceaccounts = client_v1.list_namespaced_service_account(namespace_name).items
        for serviceaccount in serviceaccounts:
            serviceaccount_name = serviceaccount.metadata.name
            if "default" and "kube-root-ca" not in serviceaccount_name:    
                print(f"\t[+] Respaldando el recurso serviceaccount llamado {serviceaccount_name}")
                yaml_output = run_command(f"kubectl get -o yaml -n {namespace_name} serviceaccount {serviceaccount_name}")
                with open(f"{namespace_dir}/serviceaccount-{serviceaccount_name}.yaml", "w") as file:
                    file.write(yaml_output)

        # Respaldar Mappings
        try:
            mappings = custom_objects_api.list_namespaced_custom_object(
                group="getambassador.io",
                version="v2",
                namespace=namespace_name,
                plural="mappings"
            )['items']
            for mapping in mappings:
                mapping_name = mapping["metadata"]["name"]
                if "default" and "kube-root-ca" not in mapping_name:
                    print(f"\t[+] Respaldando el recurso mapping llamado {mapping_name}")
                    yaml_output = run_command(f"kubectl get -o yaml -n {namespace_name} mapping {mapping_name}")
                    with open(f"{namespace_dir}/mapping-{mapping_name}.yaml", "w") as file:
                        file.write(yaml_output)
        except client.exceptions.ApiException as e:
            print(f"Error al listar mappings en el namespace {namespace_name}: {e}")

        # Respaldar Secrets
        secrets = client_v1.list_namespaced_secret(namespace_name).items
        for secret in secrets:
            secret_name = secret.metadata.name
            if "default" and "kube-root-ca" not in secret_name:
                print(f"\t[+] Respaldando el recurso secret llamado {secret_name}")
                yaml_output = run_command(f"kubectl get -o yaml -n {namespace_name} secret {secret_name}")
                with open(f"{namespace_dir}/secret-{secret_name}.yaml", "w") as file:
                    file.write(yaml_output)

        # Respaldar Configmaps
        configmaps = client_v1.list_namespaced_config_map(namespace_name).items
        if configmaps:
            for configmap in configmaps:
                configmap_name = configmap.metadata.name
                if "default" and "kube-root-ca" not in configmap_name:
                    print(f"\t[+] Respaldando el recurso configmap llamado {configmap_name}")
                    yaml_output = run_command(f"kubectl get -o yaml -n {namespace_name} configmap {configmap_name}")
                    with open(f"{namespace_dir}/configmap-{configmap_name}.yaml", "w") as file:
                        file.write(yaml_output)

print("\n[OK] Respaldo completado.")
