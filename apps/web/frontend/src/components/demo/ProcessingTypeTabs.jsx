import React from 'react'

const tabs = [
    { id: 'local', label: 'Local Processing', sub: 'Free • Privacy-first' },
    { id: 'document', label: 'Document / Writing', sub: 'Fast • No AI needed' },
    { id: 'api', label: 'API Processing', sub: 'Pro quality • API key required' },
]

/**
 * ProcessingTypeTabs component for switching between local, document, and API processing modes
 * @param {Object} props
 * @param {'local' | 'document' | 'api'} props.processingType - Current processing type
 * @param {Function} props.onProcessingTypeChange - Callback when processing type changes
 */
export const ProcessingTypeTabs = ({ processingType, onProcessingTypeChange }) => {
    return (
        <div className="flex gap-1 mb-0 flex-wrap">
            {tabs.map((tab) => {
                const active = processingType === tab.id
                return (
                    <button
                        key={tab.id}
                        onClick={() => onProcessingTypeChange(tab.id)}
                        className={`py-3 px-6 font-semibold transition-all rounded-t-lg border ${active
                            ? 'bg-gray-50 dark:bg-gray-800 border-gray-300 dark:border-gray-600 border-b-0 text-blue-600 dark:text-blue-400 relative z-10'
                            : 'bg-gray-100 dark:bg-gray-700 border-gray-300 dark:border-gray-600 border-b text-gray-600 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
                            }`}
                        style={active ? { marginBottom: '-1px' } : {}}
                    >
                        <div className="flex flex-col items-center gap-0.5">
                            <span>{tab.label}</span>
                            <span className="text-xs font-normal opacity-75">{tab.sub}</span>
                        </div>
                    </button>
                )
            })}
        </div>
    )
}


