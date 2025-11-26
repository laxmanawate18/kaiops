import React from 'react';
import { createPortal } from 'react-dom';

function ConfirmDialog({ isOpen, onClose, onConfirm, title, message, confirmText = 'Confirm', cancelText = 'Cancel', type = 'warning' }) {
  if (!isOpen) return null;

  const getTypeStyles = () => {
    switch (type) {
      case 'danger':
        return {
          icon: (
            <svg className="w-6 h-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          ),
          button: 'bg-red-600 hover:bg-red-700 focus:ring-red-500',
          ring: 'ring-red-100'
        };
      case 'warning':
        return {
          icon: (
            <svg className="w-6 h-6 text-yellow-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          ),
          button: 'bg-yellow-600 hover:bg-yellow-700 focus:ring-yellow-500',
          ring: 'ring-yellow-100'
        };
      case 'info':
        return {
          icon: (
            <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          button: 'bg-blue-600 hover:bg-blue-700 focus:ring-blue-500',
          ring: 'ring-blue-100'
        };
      default:
        return {
          icon: null,
          button: 'bg-gray-600 hover:bg-gray-700 focus:ring-gray-500',
          ring: 'ring-gray-100'
        };
    }
  };

  const styles = getTypeStyles();

  const modalContent = (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 overflow-y-auto" aria-labelledby="modal-title" role="dialog" aria-modal="true">
      {/* Background overlay */}
      <div 
        className="fixed inset-0 bg-gray-900 bg-opacity-75 transition-opacity backdrop-blur-sm z-40" 
        aria-hidden="true"
        onClick={onClose}
      ></div>

      {/* Modal content - always centered in viewport */}
      <div className="relative z-50 bg-white dark:bg-gray-800 rounded-2xl text-left overflow-hidden shadow-2xl transform transition-all w-full max-w-lg border-2 border-gray-200 dark:border-gray-700 my-8">
          <div className="bg-white dark:bg-gray-800 px-6 pt-6 pb-4">
            <div className="sm:flex sm:items-start">
              <div className={`mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full ${styles.ring} sm:mx-0 sm:h-10 sm:w-10`}>
                {styles.icon}
              </div>
              <div className="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left flex-1">
                <h3 className="text-xl font-black text-gray-900 dark:text-white leading-6" id="modal-title">
                  {title}
                </h3>
                <div className="mt-3 text-sm text-gray-600 dark:text-gray-300 leading-relaxed">
                  {typeof message === 'string' ? message : <>{message}</> }
                </div>
              </div>
            </div>
          </div>
          <div className="bg-gray-50 dark:bg-gray-900/50 px-6 py-4 sm:flex sm:flex-row-reverse gap-3">
            <button
              type="button"
              onClick={onConfirm}
              className={`w-full inline-flex justify-center rounded-lg border border-transparent shadow-md px-5 py-2.5 text-base font-bold text-white ${styles.button} focus:outline-none focus:ring-2 focus:ring-offset-2 sm:w-auto sm:text-sm transition-all`}
            >
              {confirmText}
            </button>
            <button
              type="button"
              onClick={onClose}
              className="mt-3 w-full inline-flex justify-center rounded-lg border-2 border-gray-300 dark:border-gray-600 shadow-sm px-5 py-2.5 bg-white dark:bg-gray-800 text-base font-bold text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-gray-500 sm:mt-0 sm:w-auto sm:text-sm transition-all"
            >
              {cancelText}
            </button>
          </div>
        </div>
    </div>
  );

  // Render modal using Portal to document.body to escape any scroll containers
  return createPortal(modalContent, document.body);
};

export default ConfirmDialog;
