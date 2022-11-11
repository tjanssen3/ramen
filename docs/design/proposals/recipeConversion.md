# Recipe to Velero mapping

## Overview
This document contains a mapping from a source Recipe to several Velero objects, which implement the Workflow sequence.

## Source Recipe

```yaml
kind: VolumeReplicationGroup
metadata:
  name: recipe-sample-cpd-instance
spec: 
  kubeObjectProtection:
    recipe:
      groups:
       - name: cpd-instance-resources
         labelSelector: icpdsupport/ignore-on-nd-backup
         excludedResourceTypes:
         - pv
         - pvc
         - event
         - event.events.k8s.io
      - name: cpd-instance-pre-workload-resources
        backupName: cpd-instance-resources
        excludedResources: 
        - deployments.apps
        - statefulsets.apps
        - daemonsets.apps
        - replicasets.apps
        - controllerrevisions.apps
        - cronjobs.batch
        - pods
        - operandrequests.operator.ibm.com
        - clients
        - imagetags.openshift.io
      - name: cpd-instance-workload-resources
        backupName: cpd-instance-resources
        includedResourceTypes:
        - deployments.apps
        - statefulsets.apps
        - daemonsets.apps
        - replicasets.apps
        - controllerrevisions.apps
        - cronjobs.batch
        - jobs.batch 
      - name: cpd-instance-operator-resources
        backupName: cpd-instance-resources
        includedResourceTypes:
        - operandrequests.operator.ibm.com
      hooks:
      - name: checkpoint
         type: exec
         config:
            container: main
           timeout: 1800
           onError: Fail
           command:
           - /cpdbr-scripts/cpdbr/checkpoint_create.sh
      - name: pre-workload
         type: exec
         config:
           container: main
           timeout: 600
           command:
           - /cpdbr-scripts/cpdbr/checkpoint_restore_preworkloadhooks.sh
      - name: post-workload
         type: exec
         config:
           container: main
           timeout: 3600
           command:
           - /cpdbr-scripts/cpdbr/checkpoint_restore_posthooks.sh
         initContainer:
         - name
           image
           volumeMounts:
           command:
      workflows:
      - name: backup
        sequence:  # format = type: name
        - hook: checkpoint
        - group: cpd-instance-resources
      - name: restore
        sequence:
        - group: cpd-instance-pre-workload-resources
        - hook: pre-workload
        - group: cpd-instance-workload-resources
        - hook: post-workload
        - group: cpd-instance-operator-resources
```		

## Velero Mapping

### Backup

1. velero "backup workflow" object: note that the Backup routine represents the first two items of the sequence

```yaml
apiVersion: velero.io/v1
kind: Backup
metadata: 
	name: workflow-backup
spec: 
  hooks: 
    resources: 
    - name: checkpoint
      labelSelector: 
        matchLabels:
          icpdsupport/addOnId=cpdbr,icpdsupport/app=br-service
      pre:
      - exec: 
        container: main 
        timeout: 1800
        command:
        - /cpdbr-scripts/cpdbr/checkpoint_create.sh
        - --include-namespaces=${GROUP.cpd-instance-resources.namespaces}
  labelSelector:
    matchLabels:
    - icpdsupport/ignore-on-nd-backup notin (true)
  excludedResources:  # note: includes Pods, so hooks will run
  - event
  - event.events.k8s.io 
```

### Restore 

2) velero "restore workflow" is broken into several resources: 
  a) group
  b) pod+exec hook
  c) group
  d) pod+exec hook
  e) group

2a) group

```yaml
apiVersion: velero.io/v1
kind: Restore
metadata:
  name: workflow-restore-1
spec:
  backupName: cpd-instance-resources 
  excludedResources:
  - deployments.apps
  - statefulsets.apps
  - daemonsets.apps
  - replicasets.apps
  - controllerrevisions.apps
  - cronjobs.batch
  - jobs.batch
  - pods
  - operandrequests.operator.ibm.com
  - clients
  - imagetags.openshift.io
```

  
2b) pod+exec hook #1

```yaml
apiVersion: velero.io/v1
kind: Restore
metadata: 
  name: workflow-restore-2
spec: 
  backupName: cpd-instance-resources  # backup contains Pods
  includedResources:
  - pods
  hooks:
    resources:
      postHooks:
        - exec:
            name: pre-workload
            labelSelector:
              matchLabels:
                - icpdsupport/addOnId=cpdbr,icpdsupport/app=br-service
            container: main
            waitTimeout: 600
            command: 
            - /cpdbr-scripts/cpdbr/checkpoint_restore_posthooks.sh
            - --include-namespaces=${GROUP.cpd-instance-resources.namespaces}
```

2c) group

```yaml
apiVersion: velero.io/v1 
kind: Restore 
metadata: 
  name: workflow-restore-3
spec: 
  backupName: cpd-instance-workload-resources
  includedResources:
  - deployments.apps
  - statefulsets.apps
  - daemonsets.apps
  - replicasets.apps
  - controllerrevisions.apps
  - cronjobs.batch
  - jobs.batch
```        
        
2d) pod+exec hook #2

```yaml
apiVersion: velero.io/v1
kind: Restore
metadata: 
  name: workflow-restore-4
spec: 
  backupName: cpd-instance-resources  # backup contains Pods
  includedResources:
  - pods
  hooks:
    resources:
      postHooks:
      - exec:
          name: post-workload
          labelSelector:
            matchLabels:
            - icpdsupport/addOnId=cpdbr,icpdsupport/app=br-service
          container: main
          waitTimeout: 3600
          command: 
          - /cpdbr-scripts/cpdbr/checkpoint_restore_posthooks.sh
          - --include-namespaces=${GROUP.cpd-instance-resources.namespaces}
```
          
2e) group

```yaml
apiVersion: velero.io/v1 
kind: Restore 
metadata: 
  name: workflow-restore-5
spec: 
  backupName: cpd-instance-workload-resources
  includedResources:
  - operandrequests.operator.ibm.com
```