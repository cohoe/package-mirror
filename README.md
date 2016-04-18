Package Mirror Management
=========================

## Supported Repos
* CentOS
* EPEL

More coming soon!

## How it works
The Jenkins Pipeline Builder defines all of the job configuration, including:
* Build Parameters
* Scheduling
* SCM Path
* Shell Command

Build parameters are set as environment variables. These variables are picked up and interpreted by the launcher scripts (Bash). These in turn call the actual mirror job script (Python) that bring in the packages and repodata from the remote endpoint. 

## For Package Administrators
### Red Hat-based Mirrors
Parameters:
* baseurl: The base URL of the repository. This should point to the root product directory in the upstream (ex: http://mirror.rit.edu/centos). Do not include a version directory here.
* version: The specific version to mirror (ex: 6.7)
* fspath:  The root filesystem path to store in. Similar to the baseurl, this should be for the product and not the specific version (ex: /mnt/pub/centos).
* repoonly: Mirror repodata only. Any value in this field means yes.
* http_proxy: HTTP proxy to use for connections. Protocol is required. (ex: http://proxy1.example.com:3128)

## For Developers
### Mirror Configuration
All mirror projects are currently defined in ```projects.json```. The basic skeleton project looks like:
```json
{
    "project": {
        "name": "MyProduct-Mirror", (A generic name you'll use to call the Generator)
        "product": "myproduct", (The tagged name to use in Jenkins)
        "release": "5", (Major version, used for symlinking)
        "jobs": [
            {
                "my-{{product}}-{{release}}-linker": {
                    "version": "5.1", (This is where you specify the active version)
                    "disabled": false (Turn this job on or off)
                ,
            },
            {
                "my-{{product}}-{{release}}-mirror": {
                    "version": "5.1" (individual job)
                ,
            }
        ],
        "views": [
            "MyProduct"
        ]
    }
}
```
Each mirror job corresponds to a specific version of the remote site you wish to mirror. You'll need to define templates for these jobs in another JSON file (see ```rh-templates.json``` for example). The linker job will configure a symlink for the active version. Note that not all operating systems utilize this feature. CentOS-based things do.

If you want a view to be created to automatically display all jobs of a particular product, you'll need to define it in ```views.json```. This is pretty straightforward since view support in the Generator is not that great.

### Building
You need to have the [Jenkins Pipeline Builder](https://github.com/constantcontact/jenkins_pipeline_builder) installed. After that, building the pipeline is pretty easy. 

```
generate pipeline -c config/login.json bootstrap ./pipeline $PROJECTNAME
```

Where ```$PROJECTNAME``` is one of your projects. You need to call this out specifically because the Generator does not parse for all projects.

WARNING: Your JSON must be valid! The Generator will barf on JSON that is syntactically incorrect and is not very good at telling you.

### Scripts

There are a handful of scripts for each mirror that you'll encounter (Red Hat examples are used here):
* rh-mirror-launcher.sh: Launch script for the mirror to parse environment variables
* rh-mirror.py: Script to mirror the data
* rh-linker-launcher.sh: Launch script for the linker to parse environment variables
* rh-linker.py: Links major versions to point-releases (ex: 6 -> 6.7)

## Jenkins Configuration
You need the following plugins:
* git
* timestamper
* ansicolor
* rvm
* rubyMetrics

You'll need to enable HTML markup formatting if you want the build graph to show up.

The SMTP server should also be set so that notification emails can be sent.

## Roadmap/Todo
* RPM Keys
