import React from 'react'

/**
 * ProcessingModeDescription component displays information about the selected processing mode
 * @param {Object} props
 * @param {'local' | 'document' | 'api'} props.processingType - Current processing type
 */
export const ProcessingModeDescription = ({ processingType }) => {
    return (
        <div className="mb-6">
            {processingType === 'local' && (
                <p className="text-sm text-gray-700 dark:text-gray-300">
                    Process images using open-source Focus AI models running on the backend.
                    No API key needed, completely free, and your images never leave your device.
                </p>
            )}
            {processingType === 'document' && (
                <p className="text-sm text-gray-700 dark:text-gray-300">
                    Optimized for handwriting, typed text, and drawings on paper.
                    Uses adaptive thresholding instead of AI — handles lined paper, shadows, and
                    uneven lighting without faded background artefacts.
                </p>
            )}
            {processingType === 'api' && (
                <p className="text-sm text-gray-700 dark:text-gray-300">
                    Use professional-grade cloud processing with superior quality.
                    Requires an API key from{' '}
                    <a href="https://withoutbg.com?utm_source=docker_app&utm_medium=web&utm_campaign=self_hosted&utm_content=api_description" target="_blank" rel="noopener noreferrer" className="text-blue-600 dark:text-blue-400 underline hover:text-blue-700 dark:hover:text-blue-300 font-medium">
                        withoutbg.com
                    </a>
                </p>
            )}
        </div>
    )
}








