# encoding: utf-8

class ChangeBatch:
    """
    Represents a single batch/transaction of changes to Route53

    Having such a class simplifies the handling of the change operations as
    we can use `ChangeBatch.add_change()` passing the change operation dict
    as it was returned by `compute_changes()`.
    """
    def __init__(self):
        self._changes = []

    @property
    def changes(self):
        return self._changes

    def add_change(self, change_operation: dict) -> None:
        self._changes.append(change_operation)

    def commit(self, r53, zone):
        """
        Commit the current ChangeBatch to Route53 in a single transaction
        """
        def change_to_rrset(change):
            rrset_dict = change["record"].dict(exclude_none=True)
            return {"Action": change["operation"],
                    "ResourceRecordSet": {**rrset_dict}}

        try:
            changes_list = list(map(change_to_rrset, self.changes))
            print("changes_list:", changes_list)

            response = r53.change_resource_record_sets(
                HostedZoneId=zone['id'],
                ChangeBatch={
                    'Comment': 'route53-transfer load operation',
                    'Changes': changes_list,
                })
            print(response)
            return True
        # TODO : catch specific exceptions
        except Exception as error:
            print("Exception :" + str(error))
