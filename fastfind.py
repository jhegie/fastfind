# Copyright: (c) 2020, Joshua Hegie <joshua.hegie.ctr@us.af.mil>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = '''
---
module: fastfind
short_description: Find module that ustilizes GNU find
description:
    - Locate large subsets of files with GNU find and a variety of filtering options
version_added: "2.6"
options:
  paths:
    description:
      - List of paths of directories to search. All paths must be fully qualified.
    required: true
  file_type:
    description:
      - Type of file to select.
    type: str
    default: 'file'
    required: false
    choices: [ file, directory, link ]
  perms:
    description:
      - What permissions to select against.
    type: str
    required: false
  xdev:
    description:
      - Whether or not to prevent crossing filesystem boundaries when traversing directories.
    type: bool
    default: 'yes'
    required: false
  links:
    description:
      - Whether or not to follow symbolic links when traversing diretories.
    type: bool
    default: 'no'
    required: false
  mindepth:
    description:
      - The minimum directory depth at which to consider for matches.
    type: int
    required: false
  maxdepth:
    description:
      - The maximum directory depth at which to consider for matches.
    type: int
    required: false
  user:
    description:
      - Name of the user that owns the applicable files or directories to match.
    type: str
    required: false
  group:
    description:
      - Name of the group that owns the applicable files or directories to match.
    type: str
    required: false
  name:
    description:
      - The name of the file to find
    type: str
    required: false
requirements: [ ]
author:
    - HPC Team
'''

EXAMPLES = '''
# Traverse /bin and /usr/bin looking for files with setuid or setgid
fastfind:
  paths:
    - /bin
    - /usr/bin
  xdev: yes
  perms: "/6000"
  links: no
'''
RETURN = '''
files:
    description: All matches found with the specified criteria
    returned: success
    type: list
    sample: [
         "/bin/ls",
         "/bin/find".
         ...
      ]
matched:
    description: Number of matched files
    returned: success
    type: int
    sample: 14
'''

from ansible.module_utils.basic import AnsibleModule

import os
import time

class fastfind(object):

    def __init__(self, module):
        self.module = module
        self.find_cmd = module.get_bin_path('find', True)
        self.paths = module.params.get('paths')
        self.file_type = module.params.get('file_type')[0]
        self.xdev = module.params.get('xdev')
        self.links = module.params.get('links')
        self.mindepth = module.params.get('mindepth')
        self.maxdepth = module.params.get('maxdepth')
        self.user = module.params.get('user')
        self.group = module.params.get('group')
        self.name = module.params.get('name')
        self.perms = module.params.get('perms')
        self.found = []

    def run_find(self):
        args = []
        filters = []

        filters.append('-type')
        filters.append(self.file_type)

        if self.xdev:
            args.append('-xdev')

        if self.links:
            args.append('-L')

        if self.mindepth > 0:
            filters.append('-mindepth')
            filters.append(self.mindepth)

        if self.maxdepth > 0:
            filters.append('-maxdepth')
            filters.append(self.maxdepth)

        if self.user != '':
            filters.append('-user')
            filters.append(self.user)

        if self.group != '':
            filters.append('-group')
            filters.append(self.group)

        if self.name != '':
            filters.append('-name')
            filters.append(self.name)

        if self.perms != '':
            filters.append('-perm')
            filters.append(self.perms)

        cmd_full = [[self.find_cmd], self.paths, args, filters]

        flatten = lambda l: [item for sublist in l for item in sublist]

        cmd = flatten(cmd_full)

        (rc, out, err) = self.module.run_command(cmd, check_rc=False)
        if rc != 0:
            self.module.fail_json(msg=err)

        print out

        for path in out.splitlines():
            self.found = self.found + [path]

def main():
    # define available arguments/parameters a user can pass to the module
    module_args = dict(
        paths=dict(type='list', required=True),
        file_type=dict(type='str', required=False, default='file', choices=['file', 'directory', 'link']),
        perms=dict(type='str', required=False, default=''),
        xdev=dict(type='bool', required=False, default=True),
        links=dict(type='bool', required=False, default=False),
        mindepth=dict(type='int', required=False, default=-1),
        maxdepth=dict(type='int', required=False, default=-1),
        user=dict(type='str', required=False, default=''),
        group=dict(type='str', required=False, default=''),
        name=dict(type='str', required=False, default='')
    )

    # seed the result dict in the object
    # we primarily care about changed and state
    # change is if this module effectively modified the target
    # state will include any data that you want your module to pass back
    # for consumption, for example, in a subsequent task
    result = dict(
        files = [],
        matched = 0
    )

    # the AnsibleModule object will be our abstraction working with Ansible
    # this includes instantiation, a couple of common attr would be the
    # args/params passed to the execution, as well as if the module
    # supports check mode
    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    find = fastfind(module)

    find.run_find()

    result['files'] = find.found
    result['matched'] = len(find.found)

    # in the event of a successful module execution, you will want to
    # simple AnsibleModule.exit_json(), passing the key/value results
    module.exit_json(**result)

if __name__ == '__main__':
    main()
