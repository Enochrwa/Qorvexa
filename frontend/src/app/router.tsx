import { createBrowserRouter, Navigate, type RouteObject } from 'react-router-dom'
import { RequireEditor } from '@/features/admin/guards'
import { BrowsePage } from '@/features/catalog/BrowsePage'
import { TitleDetailPage } from '@/features/catalog/TitleDetailPage'
import { ForgotPasswordPage } from '@/features/auth/ForgotPasswordPage'
import { RedirectIfAuthed, RequireAuth } from '@/features/auth/guards'
import { LoginPage } from '@/features/auth/LoginPage'
import { RegisterPage } from '@/features/auth/RegisterPage'
import { ResetPasswordPage } from '@/features/auth/ResetPasswordPage'
import { VerifyEmailPage } from '@/features/auth/VerifyEmailPage'
import { ManageProfilesPage } from '@/features/profiles/ManageProfilesPage'
import { ProfilePickerPage } from '@/features/profiles/ProfilePickerPage'
import { AppShell } from './AppShell'
import { NotFoundPage } from './NotFoundPage'

export const routes: RouteObject[] = [
  {
    element: <AppShell />,
    children: [
      { index: true, element: <Navigate to="/browse" replace /> },
      { path: 'browse', element: <BrowsePage /> },
      { path: 'titles/:slug', element: <TitleDetailPage /> },
      {
        element: <RedirectIfAuthed />,
        children: [
          { path: 'login', element: <LoginPage /> },
          { path: 'register', element: <RegisterPage /> },
        ],
      },
      { path: 'verify-email', element: <VerifyEmailPage /> },
      { path: 'forgot-password', element: <ForgotPasswordPage /> },
      { path: 'reset-password', element: <ResetPasswordPage /> },
      {
        element: <RequireAuth />,
        children: [
          { path: 'profiles', element: <ProfilePickerPage /> },
          { path: 'profiles/manage', element: <ManageProfilesPage /> },
          {
            path: 'admin',
            element: <RequireEditor />,
            children: [
              {
                // The studio is only for editors, so its code is loaded on demand.
                lazy: async () => ({
                  Component: (await import('@/features/admin/AdminLayout')).AdminLayout,
                }),
                children: [
                  { index: true, element: <Navigate to="/admin/titles" replace /> },
                  {
                    path: 'titles',
                    lazy: async () => ({
                      Component: (await import('@/features/admin/TitlesListPage')).TitlesListPage,
                    }),
                  },
                  {
                    path: 'titles/new',
                    lazy: async () => ({
                      Component: (await import('@/features/admin/TitleEditorPage')).NewTitlePage,
                    }),
                  },
                  {
                    path: 'titles/:id',
                    lazy: async () => ({
                      Component: (await import('@/features/admin/TitleEditorPage')).EditTitlePage,
                    }),
                  },
                ],
              },
            ],
          },
        ],
      },
      { path: '*', element: <NotFoundPage /> },
    ],
  },
]

export const createRouter = () => createBrowserRouter(routes)
