---
description: Dagster+ allows you to grant specific permissions to your organization's users with role-based access control (RBAC), ensuring that Dagster users have access only to what they need.
sidebar_label: Managing users
sidebar_position: 100
title: Managing users in Dagster+
---

Dagster+ allows you to grant specific permissions to your organization's users, ensuring that Dagster users have access only to what they require.

In this guide, you'll learn how to manage users and their permissions using the Dagster+ UI.

:::info Prerequisites

- A Dagster+ account
- The required [Dagster+ permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/):
  - **Organization Admins** can add, manage, and remove users
  - **Admins** can add users

:::

## Before you start

- **If System for Cross-domain Identity Management specification (SCIM) provisioning is enabled,** you'll need to add new users in your identity provider (IdP). Adding users will be disabled in Dagster+.
- **If using Google for Single sign-on (SSO)**, users must be added in Dagster+ before they can log in.
- **If using an Identity Provider (IdP) like Okta for SSO**, users must be assigned to the Dagster app in the IdP to be able to log in to Dagster+. Refer to the [SSO setup guides](/deployment/dagster-plus/authentication-and-access-control/sso/) for setup instructions for each of our supported IdP solutions.

By default, users will be granted Viewer permissions on each deployment. The default role can be adjusted by modifying the [`sso_default_role` deployment setting](/deployment/dagster-plus/full-deployments/deployment-settings-reference).

## Adding users to Dagster+

1. Sign in to your Dagster+ account.
2. Click the **user menu (your icon) > Organization Settings**.
3. Click the **Users** tab.
4. Click **Add new user.**
5. In the **User email** field, enter the user's email address.
6. Click **Add user**.

After the user is created, they will be notified via email, and you can [add the user to teams](#teams) and [assign user roles for each deployment](#user-roles).

![Screenshot of assigning roles to a user](/images/dagster-plus/features/authentication-and-access-control/adding-new-user.png)

## Adding users to teams \{#teams}

:::note

Teams are a Dagster+ Pro feature.

:::

Teams are useful for centralizing permission sets for different types of users. Refer to [Managing teams](/deployment/dagster-plus/authentication-and-access-control/rbac/teams) for more information about creating and managing teams.

![Screenshot of Managing teams page](/images/dagster-plus/features/authentication-and-access-control/mananging-teams.png)

:::note

When determining a user's level of access, Dagster+ will use the **most permissive** role assigned to the user between all of their team memberships and any individual role grants. Refer to [Managing user roles and permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) for more information.

:::

## Assigning user roles \{#user-roles}

In the **Roles** section, you can assign a [user role](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) for each deployment, granting them a set of permissions that controls their access to various features and functionalities within the platform.

1. Next to a deployment, click **Edit user role**.
2. Select the user role for the deployment. This [user role](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions) will be used as the default for all code locations in the deployment.
3. Click **Save**.
4. **Pro only**: To set permissions for individual [code locations](/deployment/code-locations/) in a deployment:
   1. Click the toggle to the left of the deployment to open a list of code locations.
   2. Next to a code location, click **Edit user role**.
   3. Select the user role for the code location.
   4. Click **Save**.
5. Repeat the previous steps for each deployment.
6. **Optional**: To change the user's permissions for branch deployments:
   1. Next to **All branch deployments**, click **Edit user role**.
   2. Select the user role to use for all branch deployments.
   3. Click **Save**.
7. Click **Done**.

## Removing users

Removing a user removes them from the organization. **Note**: If using a SAML-based SSO solution like Okta, you'll also need to remove the user from the IdP. Removing the user in Dagster+ doesn't remove them from the IdP.

1. Sign in to your Dagster+ account.
2. Click the **user menu (your icon) > Organization Settings**.
3. Click the **Users** tab.
4. Locate the user in the user list.
5. Click **Edit**.
6. Click **Remove user**.
7. When prompted, confirm the removal.

## Next steps

- Learn more about role-based access control (RBAC) in [Understanding User Roles & Permissions](/deployment/dagster-plus/authentication-and-access-control/rbac/user-roles-permissions)
- Learn more about how to manage teams in Dagster+ in [Understanding Team Management in Dagster+](/deployment/dagster-plus/authentication-and-access-control/rbac/teams)
- Learn more about SCIM provisioning in [SCIM Provisioning](/deployment/dagster-plus/authentication-and-access-control/scim)
- Learn more about authentication in the [SSO documentation](/deployment/dagster-plus/authentication-and-access-control/sso/)
