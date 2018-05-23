from app import app, db, bcrypt
import datetime
import jwt


class User(db.Model):
    """
    Table schema
    """
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(255), nullable=False)
    registered_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, email, password, role):
        self.email = email
        self.password = bcrypt.generate_password_hash(password, app.config.get('BCRYPT_LOG_ROUNDS')) \
            .decode('utf-8')
        self.role = role
        self.registered_on = datetime.datetime.now()

    def save(self):
        """
        Persist the user in the database
        :param user:
        :return:
        """
        db.session.add(self)
        db.session.commit()
        return self.encode_auth_token(self.id)

    def encode_auth_token(self, user_id):
        """
        Encode the Auth token
        :param user_id: User's Id
        :return:
        """
        try:
            payload = {
                'exp': datetime.datetime.utcnow() + datetime.timedelta(days=app.config.get('AUTH_TOKEN_EXPIRY_DAYS'),
                                                                       seconds=app.config.get(
                                                                           'AUTH_TOKEN_EXPIRY_SECONDS')),
                'iat': datetime.datetime.utcnow(),
                'sub': user_id
            }
            return jwt.encode(
                payload,
                app.config['SECRET_KEY'],
                algorithm='HS256'
            )
        except Exception as e:
            return e

    @staticmethod
    def decode_auth_token(token):
        """
        Decoding the token to get the payload and then return the user Id in 'sub'
        :param token: Auth Token
        :return:
        """
        try:
            payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
            is_token_blacklisted = BlackListToken.check_blacklist(token)
            if is_token_blacklisted:
                return 'Token was Blacklisted, Please login In'
            return payload['sub']
        except jwt.ExpiredSignatureError:
            return 'Signature expired, Please sign in again'
        except jwt.InvalidTokenError:
            return 'Invalid token. Please sign in again'

    @staticmethod
    def get_by_id(user_id):
        """
        Filter a user by Id.
        :param user_id:
        :return: User or None
        """
        return User.query.filter_by(id=user_id).first()

    @staticmethod
    def get_by_email(email):
        """
        Check a user by their email address
        :param email:
        :return:
        """
        return User.query.filter_by(email=email).first()

    def reset_password(self, new_password):
        """
        Update/reset the user password.
        :param new_password: New User Password
        :return:
        """
        self.password = bcrypt.generate_password_hash(new_password, app.config.get('BCRYPT_LOG_ROUNDS')) \
            .decode('utf-8')
        db.session.commit()


class BlackListToken(db.Model):
    """
    Table to store blacklisted/invalid auth tokens
    """
    __tablename__ = 'blacklist_token'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(255), unique=True, nullable=False)
    blacklisted_on = db.Column(db.DateTime, nullable=False)

    def __init__(self, token):
        self.token = token
        self.blacklisted_on = datetime.datetime.now()

    def blacklist(self):
        """
        Persist Blacklisted token in the database
        :return:
        """
        db.session.add(self)
        db.session.commit()

    @staticmethod
    def check_blacklist(token):
        """
        Check to find out whether a token has already been blacklisted.
        :param token: Authorization token
        :return:
        """
        response = BlackListToken.query.filter_by(token=token).first()
        if response:
            return True
        return False


class LeaveTypes(db.Model):
    """
    Class to represent the LeaveTypes model
    """
    __tablename__ = 'leaves_types'

    id = db.Column(db.Integer, primary_key=True)
    leaveType = db.Column(db.String(255), nullable=False)
    description = db.Column(db.String(500), nullable=True)
    num_of_days = db.Column(db.Integer, nullable=False)
    validity = db.Column(db.String, nullable=False)
    carry_forward = db.Column(db.String, nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_on = db.Column(db.DateTime, nullable=False)
    modified_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, leaveType, description, noOfDays, validity, carryForward, employeeId):
        self.leaveType = leaveType
        self.description = description
        self.num_of_days = noOfDays
        self.validity = validity
        self.carry_forward = carryForward
        self.employee_id = employeeId
        self.created_on = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Update the details of the LeaveType
        :param name:
        :return:
        """
        db.session.commit()

    def delete(self):
        """
        Delete a leaveType from the database
        :return:
        """
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def return_all(cls):
        return {'leave_types': list(map(lambda x: cls.to_json(x), LeaveTypes.query.all()))}

    def to_json(x):
        return {
            'id': x.id,
            'leave_type': x.leaveType,
            'validity': x.validity,
            'num_of_days': x.num_of_days,
            'description': x.description,
            'carry_forward': x.carry_forward
        }


class Leaves(db.Model):
    __tablename__ = 'leaves'

    id = db.Column(db.Integer, primary_key=True)
    leaveType = db.Column(db.Integer, db.ForeignKey('leaves_types.id'))
    description = db.Column(db.String(500), nullable=True)
    from_date = db.Column(db.DateTime, nullable=False)
    to_date = db.Column(db.DateTime, nullable=False)
    num_of_days = db.Column(db.Integer, nullable=False)
    employee_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    leave_status = db.Column(db.Integer, nullable=False)
    created_on = db.Column(db.DateTime, nullable=False)
    modified_at = db.Column(db.DateTime, nullable=False)

    def __init__(self, leaveType, description, from_date, to_date, num_of_days, employee_id, leave_status):
        self.leaveType = leaveType
        self.description = description
        self.from_date = from_date
        self.to_date = to_date
        self.num_of_days = num_of_days
        self.employee_id = employee_id
        self.leave_status = leave_status
        self.created_on = datetime.datetime.utcnow()
        self.modified_at = datetime.datetime.utcnow()

    def save(self):
        db.session.add(self)
        db.session.commit()

    def update(self):
        """
        Update the details of the Leaves
        :param name:
        :return:
        """
        db.session.commit()

    def delete(self):
        """
        Delete a leaves from the database
        :return:
        """
        db.session.delete(self)
        db.session.commit()

    @classmethod
    def return_all_leaves(cls):
        return {"leaves": list(map(lambda x: cls.to_json(x), Leaves.query.all()))}

    def to_json(leave):
        leave_type = LeaveTypes.query.filter_by(id=leave.leaveType).first()
        return {
            'status': 'success',
            'id': leave.id,
            'leave_type': leave_type.__getattribute__('leaveType'),
            'description': leave.description,
            'from_date': leave.from_date,
            'to_date': leave.to_date,
            'num_of_days': leave.num_of_days,
            'leave_status': leave.leave_status,
            'employee_id': leave.employee_id
        }