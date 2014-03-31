# Copyright 2013 Donald Stufft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from warehouse import db


class Database(db.Database):

    get_user_id = db.scalar(
        """ SELECT id
            FROM accounts_user
            WHERE username = %s
            LIMIT 1
        """
    )

    def get_user(self, name):
        query = \
            """ SELECT username, name, date_joined, email
                FROM accounts_user
                LEFT OUTER JOIN accounts_email ON (
                    accounts_email.user_id = accounts_user.id
                )
                WHERE username = %(username)s
                LIMIT 1
            """

        with self.engine.connect() as conn:
            result = conn.execute(query, username=name).first()

            if result is not None:
                result = dict(result)

            return result

    def user_authenticate(self, username, password):
        # Get the user with the given username
        query = \
            """ SELECT password
                FROM accounts_user
                WHERE username = %(username)s
                LIMIT 1
            """

        with self.engine.connect() as conn:
            password_hash = conn.execute(query, username=username).scalar()

            # If the user was not found, then return None
            if password_hash is None:
                return

            try:
                valid, new_hash = self.app.passlib.verify_and_update(
                    password,
                    password_hash,
                )
            except ValueError:
                # TODO: Log exception
                return

            if valid:
                if new_hash:
                    conn.execute(
                        """ UPDATE accounts_user
                            SET password = %(password)s
                            WHERE username = %(username)s
                        """,
                        password=new_hash,
                        username=username,
                    )
                return True
