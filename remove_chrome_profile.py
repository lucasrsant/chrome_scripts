"""
Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.    


Removes a Chrome profile given its id.

This script removes a profile from the Local State file. It does not delete the
actual profile folder from disk.
"""

import argparse
import json
import os
import sys


def get_local_state_path(canary):
  """Returns the path to the Local State file."""
  if sys.platform == 'win32':
    chrome_path = os.path.join('Google', 'Chrome SxS' if canary else 'Chrome')
    return os.path.join(os.environ['LOCALAPPDATA'], chrome_path,
                        'User Data', 'Local State')
  elif sys.platform == 'darwin':
    chrome_path = os.path.join(
        'Google',
        'Chrome Canary' if canary else 'Chrome')
    return os.path.join(
        os.path.expanduser('~'), 'Library', 'Application Support', chrome_path,
        'Local State')
  else:
    chrome_path = ('.config/google-chrome-canary'
                   if canary else '.config/google-chrome')
    return os.path.join(
        os.path.expanduser('~'), chrome_path, 'Local State')


def remove_profile(profile_id, dry_run, canary):
  """Removes a profile from the Local State file.

  Args:
    profile_id: The id of the profile to remove.
    dry_run: If true, dumps the resulting json in the screen instead of
      writing it to the file.
    canary: If true, use Chrome Canary profile path.
  """
  local_state_path = get_local_state_path(canary)
  if not os.path.exists(local_state_path):
    print(f'Error: Local State file not found at {local_state_path}')
    return

  with open(local_state_path, 'r+') as f:
    try:
      local_state = json.load(f)
    except json.JSONDecodeError:
      print(f'Error: Could not decode JSON from {local_state_path}')
      return

  info_cache = local_state.get('profile', {}).get('info_cache', {})
  if not info_cache:
    print('Error: No profiles found in Local State file.')
    return

  if profile_id not in info_cache:
    print(f'Error: Profile "{profile_id}" not found.')
    return

  del info_cache[profile_id]

  # Remove from profiles_order
  profiles_order = local_state.get('profile', {}).get('profiles_order', [])
  if profile_id in profiles_order:
    profiles_order.remove(profile_id)
  local_state['profile']['profiles_order'] = profiles_order

  # Remove from last_used
  last_used = local_state.get('profile', {}).get('last_used', None)
  if last_used == profile_id:
    local_state['profile']['last_used'] = 'Default'

  # Remove from last_active_profiles
  if ('last_active_profiles' in local_state['profile'] and
      profile_id in local_state['profile']['last_active_profiles']):
    index = local_state['profile']['last_active_profiles'].index(profile_id)
    del local_state['profile']['last_active_profiles'][index]

  # Remove from variations_google_groups
  if ('variations_google_groups' in local_state and
      profile_id in local_state['variations_google_groups']):
    del local_state['variations_google_groups'][profile_id]

  if dry_run:
    print(json.dumps(local_state, indent=2))
    return

  with open(local_state_path, 'w') as f:
    f.seek(0)
    json.dump(local_state, f, indent=2)
    f.truncate()

  print(f'Profile "{profile_id}" removed successfully.')


def main():
  parser = argparse.ArgumentParser(
      description='Remove a Chrome profile from the Local State file.')
  parser.add_argument(
      'profile_id', help='The id of the profile to remove.')
  parser.add_argument(
      '--dry-run',
      action='store_true',
      help='Dumps the resulting json in the screen instead of writing it to '
      'the file.')
  parser.add_argument(
      '--canary',
      action='store_true',
      help='Use Chrome Canary profile path.')
  args = parser.parse_args()

  remove_profile(args.profile_id, args.dry_run, args.canary)


if __name__ == '__main__':
  main()