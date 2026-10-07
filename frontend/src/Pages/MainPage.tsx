// React
import { Link } from "react-router-dom"

// AA TaxSystem
import BaseSectionHeader from "@/Components/Base/BaseHeader"

function MainPage() {
	return (
		<main>
			<BaseSectionHeader />
			<section className="mt-3 aa-panel">
				<div className="d-flex align-items-center justify-content-between gap-3">
					<span>Example Content</span>
					<Link className="aa-btn aa-btn-sm" to="styleguide/">
						Style Guide
					</Link>
				</div>
			</section>
		</main>
	)
}

export default MainPage
